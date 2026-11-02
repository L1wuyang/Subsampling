"""Resumable full-size native Experiment V with support-stable first-order steps.

Historical scientific sources are imported without edits. Independent coordinate
blocks use the identical native checkpointed adjoint; no spectral shortcut.
"""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[name] = '1'

import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time

import numpy as np

SOURCE = Path(__file__).resolve().parent
REPO = SOURCE.parents[1]
NATIVE_SOURCE = REPO / 'Experiments/experiment5_native_realdata_20261025'
sys.path.insert(0, str(NATIVE_SOURCE / 'src'))
from native_exp5 import kernel, common, formal
from native_exp5.setup import optimum
from native_exp5.data import load
from run_paths import historical_paths, verify_historical_sources

CHANGED = ('Landweber', 'Showalter', 'Nesterov')
METHODS = ('Ridge', 'Landweber', 'Showalter', 'HBF', 'Nesterov', 'SOAR')
RULES = ('UNI', 'NORM', 'LEV', 'OPT')


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def coordinate_job(task):
    outstr, oldstr, tag, method, start, stop = task
    out, old = Path(outstr), Path(oldstr)
    common.guard()
    case = out / 'targets' / tag / method
    dest = case / 'blocks' / f'{start:04d}_{stop:04d}.npz'
    if dest.exists():
        return tag, method, start, stop, 'cached'
    old, historical = historical_paths(old)
    folder = historical / 'targets' / tag
    data = load(old / 'inputs', tag)
    X = data['X']; Z = X if tag == 'gdsc' else X.T
    M = np.load(folder / 'M.npy'); C = np.load(folder / 'C.npy')
    rhs = data['y'] if tag == 'gdsc' else X.T @ data['y']
    p = read(case / 'parameters.json')
    before = time.perf_counter()
    target, J = kernel.influences(M, rhs, p, Z, None if tag == 'gdsc' else data['y'],
                                  C[start:stop], qbatch=stop-start,
                                  block=512 if tag == 'gdsc' else 4096, progress=False)
    assert np.isfinite(target).all() and np.isfinite(J).all()
    temp = dest.with_suffix('.tmp.npz'); temp.parent.mkdir(parents=True, exist_ok=True)
    np.savez(temp, target=target, J=J, elapsed=time.perf_counter()-before)
    temp.replace(dest)
    return tag, method, start, stop, time.perf_counter()-before


def fresh_draw(task):
    outstr, oldstr, tag, budget, rep, seed = task
    out, old = Path(outstr), Path(oldstr)
    flag = out / 'draws' / tag / f'r{budget}_rep{rep:03d}.json'
    if flag.exists() and read(flag).get('completed'):
        return tag, budget, rep, 24, 'cached'
    formal.HERE = old
    return (*formal.draw_worker((outstr, tag, budget, rep, seed)), 'fresh')


def prepare(out, old, protocol):
    old, historical = historical_paths(old)
    inp = read(old / 'inputs/data_manifest.json')
    target_manifest = read(historical / 'target_manifest.json')
    source_manifest = read(historical / 'frozen_sources.json')
    # Verify the exact files consumed, including unchanged copied scientific inputs.
    receipts = []
    for rel, expected in inp.items():
        p = old / 'inputs' / rel
        if p.suffix == '.npy':
            actual = digest(p); assert actual == expected, rel
            receipts.append(dict(path=str(p), sha256=actual))
    receipts.extend(verify_historical_sources(source_manifest, REPO, NATIVE_SOURCE))
    info = {}
    for tag in ('gdsc', 'year'):
        hist = historical / 'targets' / tag
        dest = out / 'targets' / tag; dest.mkdir(parents=True, exist_ok=True)
        X = np.load(old / 'inputs' / tag / 'X.npy', mmap_mode='r')
        norms = np.einsum('ij,ij->j' if tag == 'gdsc' else 'ij,ij->i', X, X)
        np.save(dest / 'atom_norms.npy', norms)
        setup = read(hist / 'setup.json')
        universal = len(norms) * float(norms.max()) / protocol['probability_floor'] * (1+1e-12)
        maxold = max(setup['models'][m]['maximum_atom_to_probability'] for m in CHANGED)
        for rule in ('UNI', 'NORM', 'LEV'):
            maxold = max(maxold, float(np.max(norms/np.load(hist/(rule+'_probability.npy')))))
        L = min(universal, max(setup['L'], 1.05 * maxold))
        for name in ('M.npy', 'C.npy', 'UNI_probability.npy', 'NORM_probability.npy', 'LEV_probability.npy'):
            rel = f'targets/{tag}/{name}'; assert digest(hist/name) == target_manifest[rel]
            shutil.copy2(hist/name, dest/name)
        for method in METHODS:
            md = dest / method; md.mkdir(exist_ok=True)
            if method in CHANGED:
                p = kernel.parameters(method, setup['models'][method]['parameters']['alpha'], L)
                if (md/'parameters.json').exists():
                    assert read(md/'parameters.json') == p
                else:
                    save(md/'parameters.json', p)
            else:
                for name in ('target.npy', 'parameters.json', 'summary.json', 'OPT_probability.npy',
                             'test_prediction.npy', 'design_prediction.npy'):
                    rel=f'targets/{tag}/{method}/{name}'
                    assert digest(hist/method/name) == target_manifest[rel]
                    shutil.copy2(hist/method/name, md/name)
        info[tag] = dict(L=L, universal_floor_bound=universal, historical_max_B=maxold,
                         input_shape=list(X.shape), output_coordinates=int(X.shape[0] if tag=='gdsc' else X.shape[1]),
                         parameters={m:read(dest/m/'parameters.json') for m in METHODS})
    save(out/'input_verification.json', dict(passed=True,files=receipts))
    save(out/'candidate_bounds.json', info)
    return info


def assemble(out, old, tag, method):
    old, historical = historical_paths(old)
    case=out/'targets'/tag/method; folder=out/'targets'/tag
    data=load(old/'inputs',tag); X=data['X']; C=np.load(folder/'C.npy'); M=np.load(folder/'M.npy')
    n=C.shape[0]; population=len(np.load(folder/'atom_norms.npy'))
    J=np.lib.format.open_memmap(case/'influences.npy',mode='w+',dtype='float64',shape=(n,population))
    target=None
    covered=np.zeros(n,dtype=bool)
    for file in sorted((case/'blocks').glob('*.npz')):
        start,stop=map(int,file.stem.split('_'))
        assert 0<=start<stop<=n and not covered[start:stop].any()
        with np.load(file) as block:
            if target is None: target=block['target'].copy()
            else: assert np.allclose(target,block['target'],rtol=1e-13,atol=1e-14)
            J[start:stop]=block['J']
            covered[start:stop]=True
    assert target is not None and covered.all()
    J.flush(); np.save(case/'target.npy',target)
    scores=np.sqrt(np.maximum(np.einsum('ij,ij->j',J,J),0)); pi=optimum(scores)
    np.save(case/'scores.npy',scores); np.save(case/'OPT_probability.npy',pi)
    den=float((C@target)@(C@target)); sumJ=np.sum(J,axis=1); constants={}
    for rule in RULES:
        prob=pi if rule=='OPT' else np.load(folder/(rule+'_probability.npy'))
        constants[rule]=max(0.,float(np.sum(scores*scores/prob)-sumJ@sumJ))/den
    assert constants['OPT'] <= min(constants.values())*(1+1e-8)
    prediction=data['E']@(X.T@target) if tag=='gdsc' else data['E']@target
    design=M@target if tag=='gdsc' else X@target
    np.save(case/'test_prediction.npy',prediction); np.save(case/'design_prediction.npy',design)
    full=dict(response_test_mse=float(np.mean((prediction-data['ey'])**2)),
              response_test_rmse=float(np.sqrt(np.mean((prediction-data['ey'])**2))), coefficient_norm_squared=den)
    setup=read(historical/'targets'/tag/'setup.json')
    summary=dict(c=setup['models'][method]['c'],full=full,constants=constants,
                 minimum_opt_probability=float(pi.min()),
                 maximum_atom_to_probability=float(np.max(np.load(folder/'atom_norms.npy')/pi)),
                 provenance='Recomputed native coordinate-block adjoints; all native updates executed.')
    save(case/'summary.json',summary)


def support_gate(out, info):
    rows=[]
    for tag in ('gdsc','year'):
        folder=out/'targets'/tag; norms=np.load(folder/'atom_norms.npy')
        for method in METHODS:
            p=read(folder/method/'parameters.json')
            for rule in RULES:
                pi=np.load(folder/(method+'/OPT_probability.npy' if rule=='OPT' else rule+'_probability.npy'))
                B=float(np.max(norms/pi)); h=p['dt']; a=h*p['eta']; q=h*h*B
                if method in CHANGED: ok=B<=info[tag]['L']*(1+1e-12) and h*B<=.9*(1+1e-12)
                elif method=='HBF': ok=0<a<=.01 and q<=2
                elif method=='SOAR': ok=q<=8
                else: ok=True
                rows.append(dict(dataset=tag,method=method,rule=rule,B=B,hB=h*B,h2B=q,h_eta=a,passed=bool(ok)))
    save(out/'support_gate.json',dict(passed=all(r['passed'] for r in rows),checks=rows))
    if not all(r['passed'] for r in rows):
        raise RuntimeError('New OPT exceeds candidate support bound. No formal draws released; enlarge bound and recompute with a new attempt directory.')


def summarize(out, old):
    import pandas as pd
    _, historical = historical_paths(old)
    data=pd.concat([pd.read_csv(p) for p in sorted((out/'draws').glob('*/*.csv'))],ignore_index=True)
    assert len(data)==12720
    assert data['status'].eq('complete').all()
    data.to_csv(out/'metrics.csv',index=False)
    keys=['dataset','method','rule','budget']
    result=data.groupby(keys,as_index=False).agg(n=('rep','size'),mean=('relative_coefficient_error','mean'),
        se=('relative_coefficient_error',lambda x:x.std(ddof=1)/math.sqrt(len(x))),
        theoretical=('theoretical_relative_mse','mean'),test_rmse=('test_response_rmse','mean'))
    result['empirical_to_first_order']=result['mean']/result['theoretical']
    result.to_csv(out/'summary.csv',index=False)
    wins=0
    for _,g in result.groupby(['dataset','method','budget']):
        opt=float(g.loc[g.rule=='OPT','mean'].iloc[0]);wins+=int(opt<g.loc[g.rule!='OPT','mean'].min())
    olddata=pd.read_csv(historical/'summary.csv')
    olddata.to_csv(out/'historical_summary_reference.csv',index=False)
    save(out/'results.json',dict(completed=True,records=len(data),cells=78,opt_lowest_empirical_mean_cells=wins,
        full_support_gate_passed=read(out/'support_gate.json')['passed'],
        full_conditional_mse_ordering_inferred=False,all_methods_fresh_draws=True,
        changed_targets=list(CHANGED),unchanged_targets_reused=['Ridge','HBF','SOAR']))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--historical-root',type=Path,required=True,
                    help='Historical experiment root or root CLI output containing exp5/')
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args();out=args.output.resolve();old,_=historical_paths(args.historical_root)
    assert read(out.parent/'pilot.json')['passed'], 'Native split-adjoint pilot must pass before formal execution'
    out.mkdir(parents=True,exist_ok=True);protocol=read(SOURCE/'protocol.json')
    if (out/'protocol.json').exists(): assert read(out/'protocol.json')==protocol
    else: save(out/'protocol.json',protocol)
    sources=[Path(__file__).resolve(),SOURCE/'protocol.json',SOURCE/'run_paths.py',SOURCE/'compare_results.py']
    hashes={str(p):digest(p) for p in sources}
    if (out/'run_source_hashes.json').exists(): assert read(out/'run_source_hashes.json')==hashes
    else: save(out/'run_source_hashes.json',hashes)
    snapshot=out/'source_snapshot';snapshot.mkdir(exist_ok=True)
    for path in sources:
        shutil.copy2(path,snapshot/path.name)
    start=time.perf_counter();info=prepare(out,old,protocol)
    save(out/'status.json',dict(phase='native_target_adjoints',completed=False,pid=os.getpid(),started=time.time()))
    jobs=[]
    # Smallest iteration counts first; the release gate still waits for all targets.
    for method in ('Nesterov','Landweber','Showalter'):
        for tag in ('gdsc','year'):
            for lo in range(0,info[tag]['output_coordinates'],8):
                hi=min(lo+8,info[tag]['output_coordinates'])
                jobs.append((str(out),str(old),tag,method,lo,hi))
    with futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending=[pool.submit(coordinate_job,t) for t in jobs]
        for count,job in enumerate(futures.as_completed(pending),1):
            result=job.result(); print('ADJOINT_BLOCK',count,len(jobs),*result,flush=True)
            save(out/'status.json',dict(phase='native_target_adjoints',completed=False,pid=os.getpid(),
                                      blocks_done=count,blocks_total=len(jobs),latest=result,elapsed=time.perf_counter()-start))
    for tag in ('gdsc','year'):
        for method in CHANGED: assemble(out,old,tag,method)
    support_gate(out,info)
    seal={str(p.relative_to(out)).replace('\\','/'):digest(p) for p in (out/'targets').rglob('*')
          if p.is_file() and 'blocks' not in p.parts}
    save(out/'target_manifest.json',seal)
    save(out/'sampling_release.json',dict(all_targets_derivatives_probabilities_frozen=True,
         full_support_gate_passed=True,files=len(seal),elapsed=time.perf_counter()-start))
    tasks=[(str(out),str(old),tag,r,rep,protocol['sampling_seed']) for tag in ('gdsc','year')
           for r in protocol[tag]['budgets'] for rep in range(protocol[tag]['repetitions'])]
    with futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending=[pool.submit(fresh_draw,t) for t in tasks]
        for count,job in enumerate(futures.as_completed(pending),1):
            result=job.result(); print('DRAW',count,len(tasks),*result,flush=True)
            save(out/'status.json',dict(phase='formal_draws',completed=False,pid=os.getpid(),
                draws_done=count,draws_total=len(tasks),latest=result,elapsed=time.perf_counter()-start))
    summarize(out,old)
    save(out/'status.json',dict(phase='result_validation',completed=False,elapsed=time.perf_counter()-start))
    from compare_results import compare_run
    compare_run(out, old)
    save(out/'status.json',dict(phase='completed',completed=True,elapsed=time.perf_counter()-start))


if __name__=='__main__':
    main()
