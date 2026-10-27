"""Chunked resource scheduling; actual steps and shared draws are unchanged."""
from .common import *
from .kernel import solve,reduce
from concurrent.futures import ProcessPoolExecutor,as_completed
import shutil
def arms(config,did):
    spec=config['main'] if did==1 else config['robustness']
    yield 'main',spec['budgets'],spec['repetitions'],METHODS,0,False
    if did==1:
        t=config['tails'];yield 'tails',t['budgets'],t['repetitions'],t['methods'],t['stream'],False
        z=config['zero_response'];yield 'zero_response',z['budgets'],z['repetitions'],METHODS,z['stream'],True
def worker(out,config,direction,did,arm,r,start,stop):
    guard();out=Path(out);tag,budgets,reps,methods,stream,zero=arm
    with np.load(out/f'{direction}_{did:02d}'/'data.npz') as raw:data={k:raw[k] for k in raw.files}
    data['direction']=direction
    if zero:data['y']=np.zeros_like(data['y'])
    setup=read(out/f'{direction}_{did:02d}'/'setup.json');tick=time.perf_counter()
    counts=counts_for(config['sampling_seed'],direction,did,r,reps,stream)[start:stop]
    states={m:[] for m in methods};ls_states=[];ranks=[];reduction=[];records=[]
    parameters_all={m:parameters(setup,r,m) for m in methods}
    for offset,count in enumerate(counts):
        rep=start+offset;M,rhs,Z,ix,weights=sketch(data,count);ls,rank=ls_reference(data,rhs,Z,ix,weights)
        reduced=reduce(M);ls_states.append(ls);ranks.append(rank);reduction.append([reduced[3],reduced[4]])
        for method in methods:
            p=parameters_all[method];begin=time.perf_counter();state=solve(M,rhs,p,reduced);secs=time.perf_counter()-begin
            states[method].append(state);finite=np.isfinite(state).all()
            values=metrics(data,state,ls,r) if finite else {k:np.nan for k in metrics(data,np.zeros_like(state),ls,r)}
            records.append(dict(direction=direction,data_id=did,arm=tag,budget=r,rep=rep,method=method,status='zero_response' if zero and finite else 'complete' if finite else 'numerical_failure',
                rank=rank,unique_objects=len(ix),spike_draws=int(count@data['spike_mask']),executed_steps=p['steps'],seconds=secs,**values))
    stem=out/f'{direction}_{did:02d}'/tag/f'r{r}_c{start:04d}'
    np.savez_compressed(stem.with_suffix('.npz'),counts=counts,ls_state=np.array(ls_states),rank=np.array(ranks),reduction_errors=np.array(reduction),**{m+'_state':np.array(v) for m,v in states.items()})
    write(stem.with_suffix('.csv'),records)
    save(stem.with_suffix('.json'),dict(completed=True,records=len(records),seconds=time.perf_counter()-tick,rep_start=start,rep_stop=stop))
    print('CHUNK_DONE',direction,did,tag,r,start,stop,round(time.perf_counter()-tick,2),flush=True)
    return len(records)
def main(args):
    guard();config=read(HERE/'formal_protocol.json');pilot=HERE/config['pilot']['directory']
    assert sha(pilot/'verification.json')==config['pilot']['verification_sha256']
    assert all(sha(HERE/k)==v for k,v in read(pilot/'frozen_sources.json').items())
    out=Path(args.output).resolve() if args.output else HERE/'outputs/formal_01';out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source_snapshot';snapshot.mkdir();files=scientific()+[HERE/'formal_protocol.json']
    for p in files:
        dest=snapshot/p.relative_to(HERE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    save(out/'frozen_sources.json',{str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in files});save(out/'protocol.json',config)
    jobspec=[];pars=[]
    # Freeze all full-data windows and method parameters before any counts.
    for direction in DIRECTIONS:
        for did in config['data_ids']:
            data=dataset(config['data_seed'],direction,did);setup=full_setup(data)
            folder=out/f'{direction}_{did:02d}';folder.mkdir()
            np.savez_compressed(folder/'data.npz',**{k:v for k,v in data.items() if k!='direction'});save(folder/'setup.json',setup)
            for arm in arms(config,did):
                tag,budgets,reps,methods,stream,zero=arm;(folder/tag).mkdir()
                for r in budgets:
                    for method in methods:pars.append(dict(direction=direction,data_id=did,arm=tag,**parameters(setup,r,method)))
                    for start in range(0,reps,10):jobspec.append((direction,did,arm,r,start,min(start+10,reps)))
    write(out/'parameters.csv',pars)
    save(out/'data_manifest.json',{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.glob('*/data.npz')})
    tick=time.perf_counter();total=0
    jobspec.sort(key=lambda t:(-t[3],t[4],t[1],t[0]))
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs=[pool.submit(worker,out,config,*spec) for spec in jobspec]
        for job in as_completed(jobs):total+=job.result()
    save(out/'execution.json',dict(completed=True,records=total,workers=args.workers,chunks=len(jobspec),seconds=time.perf_counter()-tick))
    print('FORMAL_COMPLETED',total,time.perf_counter()-tick,flush=True)
