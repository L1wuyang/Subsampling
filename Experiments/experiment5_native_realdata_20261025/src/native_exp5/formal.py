"""Seal all full targets/tangents/probabilities before fresh paired draws."""
from .common import *
from .data import load
from .setup import make
from .kernel import trajectory,reduce
from .pilot import scientific_sources
import concurrent.futures as futures
import csv,shutil

def setup_worker(args):
    out,tag,config=args
    guard();return make(out,tag,config)

def probability(folder,method,rule):
    return np.load(folder/(method+'/OPT_probability.npy' if rule=='OPT' else rule+'_probability.npy'),mmap_mode='r')

def draw_worker(task):
    outstr,tag,r,rep,seed=task;out=Path(outstr);guard();data=load(HERE/'inputs',tag);folder=out/'targets'/tag
    X=data['X'];Z=X if tag=='gdsc' else X.T;C=np.load(folder/'C.npy');M0=np.load(folder/'M.npy')
    Egram=data['E']@X.T if tag=='gdsc' else None
    if tag=='year':
        testgram=data['E'].T@data['E']/len(data['E']);testcross=data['E'].T@data['ey']/len(data['E']);testnorm=float(np.mean(data['ey']**2))
    uniforms=np.random.default_rng(np.random.SeedSequence([seed,int(tag=='year'),r,rep])).random(r)
    saved={'uniforms':uniforms};rows=[];cache={};max_reduction=0.;maxorth=0.;unstable=0
    for method in METHODS:
        p=read(folder/method/'parameters.json');target=np.load(folder/method/'target.npy');full=read(folder/method/'summary.json')
        for rule in RULES:
            key=method+'_OPT' if rule=='OPT' else ('UNI' if tag=='gdsc' and rule=='NORM' else rule)
            if key not in cache:
                pi=probability(folder,method,rule);cdf=np.cumsum(pi);cdf[-1]=1.
                indices=np.searchsorted(cdf,uniforms,side='right');ix,count=np.unique(indices,return_counts=True)
                weights=count/(r*pi[ix]);atoms=Z[:,ix];W=atoms*np.sqrt(weights)
                M=W@W.T;c=data['y'] if tag=='gdsc' else atoms@(weights*data['y'][ix])
                reduction=reduce(M);max_reduction=max(max_reduction,reduction[3]);maxorth=max(maxorth,reduction[4])
                # Diagnostic only: no change to h, k, endpoint, target, or probability.
                try:la.cholesky(p['L']*np.eye(len(M))-M,lower=True,check_finite=False);certificate=True
                except la.LinAlgError:certificate=False;unstable+=1
                cache[key]=(M,c,reduction,len(ix),certificate)
                saved[key+'_indices']=ix.astype(np.int32);saved[key+'_counts']=count.astype(np.int32)
            M,c,reduction,unique,certificate=cache[key]
            state,_=trajectory(M,c,p,reduction=reduction);saved[method+'_'+rule+'_state']=state
            status='complete' if np.isfinite(state).all() else 'numerical_failure'
            delta=state-target;den=full['full']['coefficient_norm_squared'];difference=C@delta
            squared=float(difference@difference);relative=squared/den if den>1e-24 else np.nan
            if tag=='gdsc':
                prediction=Egram@state;error=prediction-data['ey'];mse=float(error@error/len(error))
                target_prediction_difference=Egram@delta;predgap=float(target_prediction_difference@target_prediction_difference/len(error))
                design_delta=M0@delta;design_den=float((M0@target)@(M0@target))
            else:
                mse=float(state@testgram@state-2*testcross@state+testnorm);predgap=float(delta@testgram@delta)
                design_den=float(target@M0@target);design_delta=None
            design=float(design_delta@design_delta) if tag=='gdsc' else float(delta@M0@delta)
            rows.append(dict(dataset=tag,budget=r,rep=rep,method=method,rule=rule,status=status,relative_coefficient_error=relative,
                absolute_coefficient_squared_error=squared,relative_design_target_error=design/design_den if design_den>1e-24 else np.nan,
                test_target_prediction_mse=predgap,test_response_mse=mse,test_response_rmse=math.sqrt(max(0,mse)),
                theoretical_relative_mse=full['constants'][rule]/r,unique_objects=unique,prescribed_steps=p['steps'],step_bound_observed=certificate))
    dest=out/'draws'/tag/f'r{r}_rep{rep:03d}';dest.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(dest.with_suffix('.npz'),**saved)
    with dest.with_suffix('.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    save(dest.with_suffix('.json'),dict(completed=True,records=len(rows),max_reduction_error=max_reduction,max_orthogonality_error=maxorth,step_bound_violations=unstable))
    return tag,r,rep,len(rows)

def main(args):
    out=Path(args.output).resolve() if args.output else HERE/'outputs/formal_01'
    config=read(HERE/'formal_protocol.json');assert read(HERE/'outputs/pilot_02/verification.json')['passed']
    assert all(sha(HERE/k)==v for k,v in read(HERE/'outputs/pilot_02/frozen_sources.json').items())
    assert all(sha(HERE/'inputs'/k)==v for k,v in read(HERE/'inputs/data_manifest.json').items())
    out.mkdir(parents=True,exist_ok=False);save(out/'protocol.json',config)
    save(out/'frozen_sources.json',{str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in scientific_sources()+[HERE/'formal_protocol.json']})
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for name in read(out/'frozen_sources.json'):
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,dest)
    start=time.perf_counter();(out/'targets').mkdir()
    with futures.ProcessPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(setup_worker,(str(out/'targets'),tag,config)) for tag in ['gdsc','year']]
        for job in futures.as_completed(jobs):job.result()
    seal={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in (out/'targets').rglob('*') if p.is_file()}
    save(out/'target_manifest.json',seal)
    save(out/'sampling_release.json',dict(all_targets_derivatives_probabilities_frozen=True,files=len(seal),seconds_before_sampling=time.perf_counter()-start,source_hash=sha(out/'frozen_sources.json')))
    tasks=[(str(out),tag,r,rep,config['sampling_seed']) for tag in ['gdsc','year'] for r in config[tag]['budgets'] for rep in range(config[tag]['repetitions'])]
    total=0
    with futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs=[pool.submit(draw_worker,t) for t in tasks]
        for job in futures.as_completed(jobs):
            result=job.result();total+=result[-1];print('DRAW_COMPLETE',*result,'TOTAL',total,flush=True)
    save(out/'execution.json',dict(completed=True,records=total,tasks=len(tasks),seconds=time.perf_counter()-start))
    print('FORMAL_COMPLETE',total,flush=True)
