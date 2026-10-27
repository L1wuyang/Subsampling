"""Explicit same-count high-precision IV Nesterov replay, one or all samples.

Default --tiers dd executes ~106-bit arithmetic only and marks it unverified.
--tiers dd-td explicitly requests both ~106/159-bit full trajectories. Agreement
is numerical evidence, never a worst-case rounding certificate. Formal results
are read only; output must be a new or empty directory.
"""
from __future__ import annotations
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import types
import numpy as np
import pandas as pd
import mpmath as mp
from .exp34 import fresh_directory

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_INPUT=ROOT/'Experiments/experiment4_native_comprehensive_20261025/outputs/formal_01'
KERNELS=ROOT/'Experiments/numerical_stability_refinement_20261026'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def load_kernels():
    """Keep original bytes; only disable persistent caches in memory."""
    modules={};manifest={}
    previous=sys.modules.get('dd_native')
    try:
        for filename,name in [('dd_native.py','repro_precision_dd'),('td_native.py','repro_precision_td'),('precision_pilot.py','repro_precision_helper')]:
            path=KERNELS/filename;manifest[filename]=sha(path)
            source=path.read_text(encoding='utf8').replace('cache=True','cache=False')
            source=source.replace("os.environ['NUMBA_CACHE_DIR']=str(Path(__file__).resolve().parent/'outputs/numba_cache')",'')
            module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
            exec(compile(source,str(path),'exec'),module.__dict__)
            modules[filename]=module
            if filename=='dd_native.py':sys.modules['dd_native']=module
    finally:
        if previous is None:sys.modules.pop('dd_native',None)
        else:sys.modules['dd_native']=previous
    return modules['dd_native.py'],modules['td_native.py'],modules['precision_pilot.py'],manifest


def td_matrix(array):
    def scalar(parts):return sum(mp.mpf(float(q)) for q in parts)
    if array.ndim==2:return mp.matrix([scalar(row) for row in array])
    return mp.matrix([[scalar(array[i,j]) for j in range(array.shape[1])] for i in range(array.shape[0])])


def split_td(values):
    out=np.zeros((len(values),3))
    for i,value in enumerate(values):
        for j in range(3):out[i,j]=float(value);value-=mp.mpf(out[i,j])
    return out


def arithmetic_checks(dd,td):
    rng=np.random.default_rng(2026102706);ddworst=mp.mpf(0);tdworst=mp.mpf(0)
    for _ in range(100):
        a=rng.normal(size=3)*[1.,1e-16,1e-32];b=rng.normal(size=3)*[1.,1e-16,1e-32]
        da=sum(mp.mpf(float(v)) for v in a[:2]);db=sum(mp.mpf(float(v)) for v in b[:2])
        ta=sum(mp.mpf(float(v)) for v in a);tb=sum(mp.mpf(float(v)) for v in b)
        for op in ['add','mul']:
            q=getattr(dd,op)(*a[:2],*b[:2]);value=sum(mp.mpf(float(v)) for v in q)
            ddworst=max(ddworst,abs(value-(da+db if op=='add' else da*db)))
            q=getattr(td,op)(*a,*b);value=sum(mp.mpf(float(v)) for v in q)
            tdworst=max(tdworst,abs(value-(ta+tb if op=='add' else ta*tb)))
    if ddworst>=mp.mpf('1e-28') or tdworst>=mp.mpf('1e-43'):
        raise ArithmeticError('Floating expansion arithmetic self-check failed')
    return dict(dd_max_absolute_error=mp.nstr(ddworst,20),td_max_absolute_error=mp.nstr(tdworst,20),sampled_operands=100,
                scope='Sample arithmetic self-check, not a uniform proof for all possible operands.')


def one_tier(dd,td,helper,X,y,counts,N,h,steps,tier,column):
    tick=time.perf_counter()
    if tier=='dd':
        Mh,Ml,ch,cl=dd.weighted_gram(X,y,counts,N,column)
        M=helper.matrix(Mh,Ml);rhs=helper.matrix(ch,cl)
    else:
        parts,forcing=td.weighted_gram(X,y,counts,N,column)
        M=td_matrix(parts);rhs=td_matrix(forcing)
    Q,T,reconstruction=helper.tridiagonal(M);c=Q.T*rhs
    ls=mp.lu_solve(M,rhs)
    if mp.norm(M*ls-rhs)/max(1,mp.norm(rhs))>=mp.mpf('1e-65'):
        raise ArithmeticError('High-precision LS residual check failed')
    count=min(200,steps);a=mp.matrix(len(c),1);old=a.copy()
    for j in range(1,count+1):
        z=a+mp.mpf(max(j-2,0))/j*(a-old);old,a=a,z+mp.mpf(h)*(c-T*z)
    if tier=='dd':
        dh,dl=helper.split([T[i,i] for i in range(len(c))]);oh,ol=helper.split([T[i+1,i] for i in range(len(c)-1)]);rh,rl=helper.split(c)
        def execute(k):
            high,low=dd.nesterov(dh,dl,oh,ol,rh,rl,h,k,True)
            return helper.matrix(high,low)
        tolerance=mp.mpf('1e-25')
    else:
        diag=split_td([T[i,i] for i in range(len(c))]);off=split_td([T[i+1,i] for i in range(len(c)-1)]);forcing=split_td(c)
        def execute(k):return td_matrix(td.nesterov(diag,off,forcing,h,k))
        tolerance=mp.mpf('1e-39')
    prefix=mp.norm(execute(count)-a)/max(1,mp.norm(a))
    if prefix>=tolerance:raise ArithmeticError(f'{tier} literal prefix self-check failed')
    state=Q*execute(steps)
    C=mp.matrix(X.T.tolist()) if column else mp.eye(len(state))
    beta=C*state;betaLS=C*ls;gapvector=beta-betaLS;gap=mp.norm(gapvector)
    return dict(state=state,beta=beta,ls=betaLS,gapvector=gapvector,gap=gap,
                report=dict(tier=tier,steps=steps,all_updates_executed=True,
                    prefix_check_steps=count,prefix_relative_error=mp.nstr(prefix,25),
                    householder_relative_residual=mp.nstr(reconstruction,25),
                    gap_norm=mp.nstr(gap,55),scaled_squared_gap=mp.nstr(N*gap**2,55),seconds=time.perf_counter()-tick))


def replay(direction,budget,reps,output,*,rep_start=0,tiers='dd',input_dir=DEFAULT_INPUT,relative_tolerance=1e-6):
    input_dir=Path(input_dir).expanduser().resolve();output=Path(output).expanduser().resolve()
    if output==input_dir or output.is_relative_to(input_dir):raise ValueError('Precision output must be outside its input archive')
    mp.mp.dps=90
    folder=input_dir/f'{direction}_01'
    with np.load(folder/'data.npz') as raw:X=raw['X'];y=raw['y']
    parameters=pd.read_csv(input_dir/'parameters.csv',float_precision='round_trip')
    p=parameters[(parameters.direction==direction)&(parameters.data_id==1)&(parameters.arm=='main')&
                 (parameters.method=='Nesterov')&(parameters.budget==budget)]
    if len(p)!=1:raise ValueError('Budget is absent from the first formal data set')
    p=p.iloc[0];steps=int(p.steps);h=float(p['dt'])
    chunks=[];available=set();manifest={}
    for path in sorted((folder/'main').glob(f'r{budget}_c*.npz')):
        meta=path.with_suffix('.json');info=json.loads(meta.read_text(encoding='utf8'))
        chunks.append((path,info));available.update(range(info['rep_start'],info['rep_stop']))
    requested=list(range(rep_start,rep_start+reps))
    if not set(requested).issubset(available):raise ValueError('Requested repetitions are absent from saved counts')
    output=fresh_directory(output)
    for path in [folder/'data.npz',input_dir/'parameters.csv',input_dir/'protocol.json']:
        manifest[path.relative_to(input_dir).as_posix()]=sha(path)
    dd,td,helper,kernel_hashes=load_kernels()
    protocol=dict(direction=direction,data_id=1,budget=budget,rep_start=rep_start,repetitions=reps,tiers=tiers,
        relative_agreement_tolerance=relative_tolerance,steps=steps,h_binary64=h,
        input_semantics='Exact original binary64 X/y; rational repeated-count weights and momentum; same original h and step count; complete literal trajectories.',
        formal_results_replaced=False,accuracy_certified=False,kernel_sha256=kernel_hashes,
        cache_policy='Original files unchanged; loaded in memory with persistent cache disabled.')
    save(output/'precision_protocol.json',protocol)
    save(output/'arithmetic_self_checks.json',arithmetic_checks(dd,td))
    rows=[];tick=time.perf_counter()
    for rep in requested:
        path,meta=next((p,m) for p,m in chunks if m['rep_start']<=rep<m['rep_stop'])
        for q in [path,path.with_suffix('.json')]:manifest[q.relative_to(input_dir).as_posix()]=sha(q)
        with np.load(path) as raw:
            j=rep-meta['rep_start'];counts=raw['counts'][j];rank=int(raw['rank'][j])
        sample=output/f'rep_{rep:04d}';sample.mkdir()
        row=dict(rep=rep,rank=rank,steps=steps,status='unresolved',accuracy_certified=False)
        if rank<X.shape[0 if direction=='column' else 1]:
            row.update(status='unresolved_rank_deficient_reference',trajectory_executed=False,
                       limitation='This high-budget replay driver requires a full-rank reference; no arbitrary-rank inverse is substituted.')
        else:
            try:
                a=one_tier(dd,td,helper,X,y,counts,budget,h,steps,'dd',direction=='column');row['dd']=a['report']
                save(sample/'dd_state.json',[mp.nstr(v,85) for v in a['state']])
                row.update(status='not_crosschecked',trajectory_executed=True)
                if tiers=='dd-td':
                    b=one_tier(dd,td,helper,X,y,counts,budget,h,steps,'td',direction=='column');row['td']=b['report']
                    save(sample/'td_state.json',[mp.nstr(v,85) for v in b['state']])
                    coef=mp.norm(a['beta']-b['beta']);ls=mp.norm(a['ls']-b['ls']);gapchange=mp.norm(a['gapvector']-b['gapvector'])
                    scale=max(b['gap'],mp.mpf('1e-80'));ratio=max(coef,ls,gapchange)/scale
                    agreed=ratio<=mp.mpf(relative_tolerance)
                    row.update(status='tier_agreement' if agreed else 'unresolved_tier_disagreement',
                        coefficient_tier_change=mp.nstr(coef,55),LS_tier_change=mp.nstr(ls,55),gap_vector_tier_change=mp.nstr(gapchange,55),
                        maximum_change_over_td_gap=mp.nstr(ratio,35),tier_agreement=agreed)
            except (ArithmeticError,ValueError,ZeroDivisionError,np.linalg.LinAlgError) as error:
                row.update(status='unresolved_numerical_failure',error_type=type(error).__name__,error=str(error))
        rows.append(row);save(sample/'sample_report.json',row)
        print('PRECISION_SAMPLE',direction,budget,rep,row['status'],flush=True)
    all_agree=bool(rows and all(q['status']=='tier_agreement' for q in rows))
    summary=dict(completed=True,samples=rows,requested_repetitions=reps,
        available_formal_repetitions=len(available),full_formal_group_coverage=set(requested)==available,
        all_requested_samples_have_two_tier_agreement=all_agree,accuracy_certified=False,
        formal_means_replaced=False,seconds=time.perf_counter()-tick,
        limitation='Two arithmetic tiers and prefix checks provide numerical evidence for explicitly requested samples only; never a uniform rounding certificate.')
    if all_agree:
        summary['refined_requested_sample_mean_scaled_gap']=mp.nstr(sum(mp.mpf(q['td']['scaled_squared_gap']) for q in rows)/len(rows),55)
    save(output/'precision_summary.json',summary);save(output/'input_sha256.json',manifest)
    for relative,digest in manifest.items():
        if sha(input_dir/relative)!=digest:raise AssertionError('Input changed during read-only replay')
    for name,digest in kernel_hashes.items():
        if sha(KERNELS/name)!=digest:raise AssertionError('Precision scientific source changed')
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--direction',choices=['column','row'],required=True)
    parser.add_argument('--budget',type=int,required=True)
    parser.add_argument('--reps',type=int,default=1)
    parser.add_argument('--rep-start',type=int,default=0)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True,help='Your newly generated IV result directory; no historical states are bundled.')
    parser.add_argument('--tiers',choices=['dd','dd-td'],default='dd')
    parser.add_argument('--relative-tolerance',type=float,default=1e-6)
    args=parser.parse_args(argv)
    if args.budget<2 or args.reps<1 or args.rep_start<0 or not args.relative_tolerance>0:
        parser.error('Require budget>=2, reps>=1, rep-start>=0 and a positive relative tolerance')
    summary=replay(args.direction,args.budget,args.reps,args.output,rep_start=args.rep_start,
                   tiers=args.tiers,input_dir=args.input,relative_tolerance=args.relative_tolerance)
    print(json.dumps(dict(completed=True,samples=len(summary['samples']),two_tier_agreement=summary['all_requested_samples_have_two_tier_agreement'],accuracy_certified=False)),flush=True)
    if any(q['status'].startswith('unresolved') for q in summary['samples']):
        raise SystemExit(2)


if __name__=='__main__':main()
