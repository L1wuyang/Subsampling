"""Execute a frozen, independently seeded experiment; never overwrite a run."""
from native import *
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib,json,csv,shutil,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs/formal_01'
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def write(path,rows):
    with Path(path).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def metrics(U,ref,X,H,y,beta,noise,scales):
    B=U@X;target=X.T@ref;delta=B-beta;signal=X@beta
    gap=np.sum((B-target)**2,axis=1);norm=float(target@target)
    future_denom=float(np.sum((scales*beta)**2)/len(y))
    future=np.sum((delta*scales)**2,axis=1)/len(y)
    return dict(absolute_gap=gap,relative_gap=gap/norm if norm>1e-24 else np.full(len(U),np.nan),
                true_coef_rel_sq=np.sum(delta**2,axis=1)/float(beta@beta),
                design_signal_rel_sq=np.sum((B@X.T-signal)**2,axis=1)/float(signal@signal),
                population_signal_rel_sq=future/future_denom,population_response_mse=future+noise**2,
                residual_norm=np.linalg.norm(y-U@H.T,axis=1))

def load(did,arm):
    with np.load(HERE/'data'/f'data_{did:02d}.npz') as a:
        G=a['G'];z=a['scale_z'];beta=a['beta0'];e=a['standard_noise']
    scales=np.exp(arm['heterogeneity']*z);scales=np.minimum(scales,np.quantile(scales,.98,method='linear'));scales/=np.sqrt(np.mean(scales**2))
    X=G*scales/np.sqrt(len(e));y=X@beta+arm['sigma']*e
    if arm.get('zero_response'):y=np.zeros_like(y)
    return X,y,beta,scales

def run_arm(did,arm,config):
    start=time.perf_counter();folder=OUT/f'data_{did:02d}'/arm['tag'];folder.mkdir(parents=True,exist_ok=False)
    X,y,beta,scales=load(did,arm);H,ps,models,history=setup(X,y,arm['c'],arm['floor'])
    print('SETUP_DONE',did,arm['tag'],'seconds',time.perf_counter()-start,'L',history[-1]['L'],flush=True)
    save(folder/'bound_history.json',history)
    refs=[];traces=[];costs=[];states={**ps,'y':y,'scales':scales}
    for method,m in models.items():
        param=m['param'];u=m['u'];J=m['J'];scores=m['scores'];pi=m['pi']
        one=metrics(u[None],u,X,H,y,beta,arm['sigma'],scales)
        rowspace=1-float((X@beta)@sla.solve(H,X@beta,assume_a='pos'))/float(beta@beta)
        refs.append(dict(data_id=did,arm=arm['tag'],method=method,**{k:v for k,v in param.items() if k!='method'},
                         target_norm_sq=float((X.T@u)@(X.T@u)),rowspace_coef_floor=rowspace,
                         status='zero_target' if np.linalg.norm(X.T@u)<=1e-12 else 'complete',
                         **{key:float(value[0]) for key,value in one.items()}))
        center=float(J.sum(axis=1)@H@J.sum(axis=1));local=[]
        for rule,prob in {**ps,'OPT':pi}.items():
            val=float(np.sum(scores**2/prob)-center);local.append(val)
            traces.append(dict(data_id=did,arm=arm['tag'],method=method,rule=rule,local_trace=val,
                               normalized_trace=val/refs[-1]['target_norm_sq'] if refs[-1]['target_norm_sq']>1e-24 else np.nan))
        assert local[-1]<=min(local)+1e-8*max(1,max(local))
        states[method+'_u']=u;states[method+'_J']=J;states[method+'_pi']=pi;states[method+'_scores']=scores
    np.savez_compressed(folder/'native_states.npz',**states);write(folder/'full_reference.csv',refs);write(folder/'local_trace.csv',traces)
    save(folder/'parameters.json',{method:m['param'] for method,m in models.items()})
    rows=[]
    for r in arm['budgets']:
        uniforms=np.random.default_rng(np.random.SeedSequence([config['sampling_seed'],did,r,arm['stream']])).random((arm['repetitions'],r))
        shared={rule:matrices(X,pi,uniforms) for rule,pi in ps.items()};raw=dict(uniforms=uniforms)
        for method,m in models.items():
            tick=time.perf_counter();Ms=np.concatenate([shared[rule] for rule in RULES[:3]]+[matrices(X,m['pi'],uniforms)])
            U=batch(Ms,y,m['param']);raw[method+'_u']=U
            mm=metrics(U,m['u'],X,H,y,beta,arm['sigma'],scales);finite=np.isfinite(U).all(axis=1)
            for ri,rule in enumerate(RULES):
                for rep in range(arm['repetitions']):
                    i=ri*arm['repetitions']+rep
                    rows.append(dict(data_id=did,arm=arm['tag'],budget=r,method=method,rule=rule,rep=rep,
                                     status=('zero_target' if refs[METHODS.index(method)]['status']=='zero_target' else 'complete') if finite[i] else 'numerical_failure',
                                     executed_steps=m['param']['steps'],dt=m['param']['dt'],
                                     **{key:float(value[i]) for key,value in mm.items()}))
            costs.append(dict(data_id=did,arm=arm['tag'],method=method,budget=r,seconds=time.perf_counter()-tick,
                              trajectory_labels=len(U),updates=int(len(U)*m['param']['steps']),
                              rhs_evaluations=int(len(U)*m['param']['steps']*(4 if method in ['Showalter','HBF','SOAR'] else 1)),
                              direct_solves=int(len(U)) if method=='Ridge' else 0))
        np.savez_compressed(folder/f'raw_r{r}.npz',**raw)
        print('BUDGET_DONE',did,arm['tag'],r,flush=True)
    write(folder/'results.csv',rows);write(folder/'costs.csv',costs)
    result=dict(data_id=did,arm=arm['tag'],rows=len(rows),seconds=time.perf_counter()-start)
    save(folder/'completion.json',result);return result

def worker(did,config):
    guard();result=[]
    for arm in config['arms']:
        if did in arm['data_ids']:result.append(run_arm(did,arm,config))
    return result

def main():
    guard();config=json.loads((HERE/'formal_protocol.json').read_text(encoding='utf8'));pilot=json.loads((HERE/'outputs/pilot_02/verification.json').read_text(encoding='utf8'))
    assert pilot['passed'];assert digest(HERE/'native.py')==digest(HERE/'outputs/pilot_02/source_snapshot/native.py')
    OUT.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    protected=json.loads((HERE/'protected_before.json').read_text(encoding='utf8'));assert all(digest(ROOT/k)==v for k,v in protected.items())
    snapshot=OUT/'source_snapshot';snapshot.mkdir();names=['native.py','pilot.py','run_formal.py','formal_protocol.json']
    for name in names:shutil.copy2(HERE/name,snapshot/name)
    frozen={name:digest(HERE/name) for name in names};save(OUT/'frozen_sources.json',frozen);save(OUT/'protocol.json',config);save(OUT/'pilot_acceptance.json',pilot)
    (HERE/'data').mkdir(exist_ok=False);manifest=[]
    for did in config['data_ids']:
        rg=np.random.default_rng(np.random.SeedSequence([config['data_seed'],did]));n,p=config['n'],config['p']
        G=rg.normal(size=(n,p));z=rg.normal(size=p);beta=rg.normal(size=p);beta/=np.linalg.norm(beta);e=rg.normal(size=n)
        path=HERE/'data'/f'data_{did:02d}.npz';np.savez_compressed(path,G=G,scale_z=z,beta0=beta,standard_noise=e)
        manifest.append(dict(data_id=did,sha256=digest(path)))
    save(OUT/'data_manifest.json',manifest);completions=[]
    with ProcessPoolExecutor(max_workers=config['workers']) as pool:
        tasks=[pool.submit(worker,did,config) for did in config['data_ids']]
        for fut in as_completed(tasks):
            completions.extend(fut.result());print('DATA_DONE',json.dumps(completions[-1]),flush=True)
    import pandas as pd
    for name in ['results','full_reference','local_trace','costs']:
        main=[];extra=[]
        for did in config['data_ids']:
            for arm in config['arms']:
                if did in arm['data_ids']:
                    df=pd.read_csv(OUT/f'data_{did:02d}'/arm['tag']/(name+'.csv'))
                    (main if arm['tag']=='main' else extra).append(df)
        pd.concat(main,ignore_index=True).to_csv(OUT/(name+'.csv'),index=False)
        pd.concat(extra,ignore_index=True).to_csv(OUT/('sensitivity_'+name+'.csv'),index=False)
    assert all(digest(HERE/k)==v for k,v in frozen.items());assert all(digest(ROOT/k)==v for k,v in protected.items())
    save(OUT/'execution.json',dict(completed=True,seconds=time.perf_counter()-start,completions=completions,
                                  protected_files_unchanged=len(protected),frozen_sources_unchanged=True,spectral_guard_active=True))
    print('ALL_COMPLETE',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
