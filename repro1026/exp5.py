"""Portable Experiment V: rebuild inputs, execute native maps, report empirical means.

The archived scientific bodies are imported unchanged. All new artifacts are
written under a fresh --output directory; source archives are never updated.
Historical two-sided mean tests are available explicitly, but are not part of
the default finite-repetition report or evidence for full conditional MSE order.
"""
from __future__ import annotations
import argparse, concurrent.futures, gzip, hashlib, importlib, json, math, os
from pathlib import Path
import shutil, sys, time
from types import SimpleNamespace
sys.dont_write_bytecode=True
for _key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS']:
    os.environ.setdefault(_key, '1')
import numpy as np
import pandas as pd
from scipy.stats import t, ttest_rel

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = 'experiment5_native_realdata_20261025'
METHODS = ['Ridge','Landweber','Showalter','HBF','Nesterov','SOAR']
RULES = ['UNI','NORM','LEV','OPT']
RAW = {
 'expression':'Data/real_data_20261016/raw/gdsc/expression_release_6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz',
 'response':'Data/real_data_20261016/raw/gdsc/response_release_8.4/GDSC2_fitted_dose_response_24Jul22.csv',
 'year':'Data/real_data_20261016/raw/yearpredictionmsd/yearpredictionmsd/YearPredictionMSD.txt',
}
RAW_SHA = {
 'expression':'90fe07de1a72fa9f4fdcbdfc0c0bb23c70b1435bac2adad7e99c2f2bb154ca93',
 'response':'9d6dc82b9a072bb00b6139dcd6c4c11de1e047f210382fb726e92ab8dd0eae2a',
 'year':'4b6f8e50235b359e01689ae7fb33ad0f89677e9a15f25f3d6259327a6bb927bb',
}

def assert_writable_output(path,project_root=None):
    """Reject the package/source roots, their ancestors and every frozen tree."""
    output=Path(path).expanduser().resolve()
    roots={PACKAGE_ROOT.resolve(),Path(project_root or PACKAGE_ROOT).resolve()}
    for base in roots:
        if output==base or base.is_relative_to(output):
            raise ValueError(f'Output cannot be a package/source root or its ancestor: {output}')
        for name in ['Experiments','Data','Paper_Versions','provenance','repro1026']:
            frozen=base/name
            if output.is_relative_to(frozen):
                raise ValueError(f'Output must be outside frozen {frozen}')
    return output

def new_output(path,project_root=None):
    output=assert_writable_output(path,project_root)
    if output.exists():raise FileExistsError(f'Choose a fresh output directory; refusing to overwrite {output}')
    output.mkdir(parents=True)
    return output

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def normalize(train, test, y, ey):
    mean=train.mean(0);scale=train.std(0);keep=scale>1e-12;ym=float(y.mean())
    if not all(np.isfinite(a).all() for a in [train,test,y,ey]):
        raise ValueError('Nonfinite raw input; no success-only filtering is allowed.')
    return ((train[:,keep]-mean[keep])/scale[keep],
            (test[:,keep]-mean[keep])/scale[keep],y-ym,ey-ym,
            dict(mean=mean,scale=scale,keep=keep,response_mean=ym))

def prepare_inputs(project_root, destination, mode='formal'):
    """Use separately acquired official raw bytes and frozen cell IDs."""
    project_root=Path(project_root).resolve();destination=new_output(destination,project_root)
    split_path=project_root/'provenance/exp5_inputs/gdsc_split.json'
    if not split_path.is_file():
        raise FileNotFoundError(f'Frozen split manifest missing: {split_path}')
    split=read(split_path)
    sources={key:project_root/value for key,value in RAW.items()}
    for key,path in sources.items():
        if not path.is_file():raise FileNotFoundError(f'Raw input missing: {path}. Run python run.py data download --dataset all, or follow docs/DATA_SOURCES_CN.md.')
        if sha(path)!=RAW_SHA[key]:raise ValueError(f'Raw input hash mismatch: {path}')
    with gzip.open(sources['expression'],'rt',encoding='utf-8') as stream:
        ids=list(map(int,stream.readline().rstrip().split('\t')[1:]))
    table=pd.read_csv(sources['expression'],sep='\t',compression='gzip')
    genes=table.iloc[:,0].astype(str).to_numpy()
    keep_gene=~pd.Series(genes).duplicated(keep=False).to_numpy()
    counts=pd.Series(ids).value_counts();lookup={v:j for j,v in enumerate(ids) if counts[v]==1}
    expression=table.iloc[:,1:].to_numpy(dtype=float)[keep_gene]
    response=pd.read_csv(sources['response']);drug=response[response.DRUG_ID==1862]
    usable={v for v,j in lookup.items() if np.isfinite(expression[:,j]).all()}
    pairs=drug[drug.COSMIC_ID.isin(usable)&np.isfinite(drug.LN_IC50)].sort_values('COSMIC_ID')
    if not pairs.COSMIC_ID.is_unique:raise ValueError('Response identifiers are not unique.')
    if pairs.COSMIC_ID.astype(int).tolist()!=split['matched_ids']:
        raise ValueError('Matched complete GDSC cell set differs from the frozen protocol.')
    ids_all=pairs.COSMIC_ID.to_numpy();position={int(v):j for j,v in enumerate(ids_all)}
    train=np.array([position[int(v)] for v in split['train_ids']],dtype=int)
    test=np.array([position[int(v)] for v in split['test_ids']],dtype=int)
    X=expression[:,[lookup[int(v)] for v in ids_all]].T.copy();y=pairs.LN_IC50.to_numpy()
    if X.shape!=(937,17737):raise ValueError(f'Unexpected full GDSC shape {X.shape}')
    if set(train)&set(test) or sorted(np.r_[train,test].tolist())!=list(range(937)):
        raise ValueError('Frozen GDSC split is not an exhaustive disjoint partition.')
    selected_genes=genes[keep_gene]
    if mode=='smoke':
        train=train[:24];test=test[:8];X=X[:,:32];selected_genes=selected_genes[:32]
    T,E,ty,ey,prep=normalize(X[train],X[test],y[train],y[test])
    folder=destination/'gdsc';folder.mkdir()
    for name,array in [('X',T),('E',E),('y',ty),('ey',ey)]:np.save(folder/(name+'.npy'),array)
    np.savez_compressed(folder/'preprocessing.npz',**prep,train=train,test=test,
                        train_ids=ids_all[train],test_ids=ids_all[test],genes=selected_genes)
    del table,expression,X,T,E
    # Reproduce the frozen full-data parse exactly; smoke selects raw rows before fitting.
    arr=pd.read_csv(sources['year'],header=None).to_numpy(dtype=float)
    if arr.shape!=(515345,91):raise ValueError(f'Unexpected Year shape {arr.shape}')
    train=np.arange(463715);test=np.arange(463715,515345)
    if mode=='smoke':
        train=train[:64];test=test[:16];arr=arr[:,:17]
        T,E,ty,ey,prep=normalize(arr[train,1:],arr[test,1:],arr[train,0],arr[test,0])
    else:
        # Preserve the frozen prefix-view layout and reduction order, as well as its values.
        T,E,ty,ey,prep=normalize(arr[:463715,1:],arr[463715:,1:],arr[:463715,0],arr[463715:,0])
    folder=destination/'year';folder.mkdir()
    for name,array in [('X',T),('E',E),('y',ty),('ey',ey)]:np.save(folder/(name+'.npy'),array)
    np.savez_compressed(folder/'preprocessing.npz',**prep,train=train,test=test)
    source_manifest={RAW[key]:RAW_SHA[key] for key in RAW}
    source_manifest[str(split_path.relative_to(project_root)).replace('\\','/')]=sha(split_path)
    write(destination/'source_manifest.json',source_manifest)
    metadata={'mode':mode,'role':'formal reproduction' if mode=='formal' else 'small implementation smoke; not paper evidence',
              'training_preprocessing_refitted':True,'old_input_cache_required':False,'datasets':{}}
    for tag in ['gdsc','year']:
        metadata['datasets'][tag]={key:list(np.load(destination/tag/(key+'.npy'),mmap_mode='r').shape) for key in ['X','E','y','ey']}
    write(destination/'preflight.json',metadata)
    write(destination/'data_manifest.json',{str(p.relative_to(destination)).replace('\\','/'):sha(p) for p in destination.rglob('*') if p.is_file() and p.name!='data_manifest.json'})
    return metadata

def scientific_modules(project_root, run_root):
    """Redirect only run-local inputs/cache; never patch archived file bodies."""
    project_root=Path(project_root).resolve();run_root=Path(run_root).resolve()
    os.environ['NUMBA_CACHE_DIR']=str(run_root/'numba_cache')
    src=project_root/'Experiments'/EXPERIMENT/'src'
    if not (src/'native_exp5/kernel.py').is_file():raise FileNotFoundError(src)
    if str(src) not in sys.path:sys.path.insert(0,str(src))
    modules={name:importlib.import_module('native_exp5.'+name) for name in ['common','data','kernel','setup','formal','analyze']}
    for module in modules.values():module.HERE=run_root;module.ROOT=project_root
    return modules

def _target_job(task):
    project,run,formal,tag,config,stable=task
    mods=scientific_modules(project,run);mods['common'].guard()
    if config.get('reproduction_mode')=='smoke':
        mods['setup'].HISTORIC_C={tag:{m:1. for m in METHODS} for tag in ['gdsc','year']}
    if stable:
        from .v_stability import build_targets
        return build_targets(Path(formal)/'targets',tag,config,mods)
    return mods['setup'].make(Path(formal)/'targets',tag,config)

def _draw_job(task):
    project,run,payload=task
    mods=scientific_modules(project,run)
    return mods['formal'].draw_worker(payload)

def holm(values):
    values=np.asarray(values,dtype=float);result=np.empty(len(values));running=0.
    for rank,index in enumerate(np.argsort(values,kind='stable')):
        running=max(running,(len(values)-rank)*values[index]);result[index]=min(1.,running)
    return result

def paired_comparisons(frame, budgets, alternative='two-sided'):
    rows=[]
    for tag,budget in budgets.items():
        for method in METHODS:
            g=frame[(frame.dataset==tag)&(frame.budget==budget)&(frame.method==method)].pivot(index='rep',columns='rule',values='relative_coefficient_error').sort_index()
            if set(g.columns)!=set(RULES) or g.isna().any().any() or len(g)<2:
                raise ValueError(f'Incomplete paired family {tag}/{method}/{budget}')
            for rule in RULES[:-1]:
                d=(g.OPT-g[rule]).to_numpy();n=len(d);se=float(d.std(ddof=1)/math.sqrt(n));mean=float(d.mean());half=float(t.ppf(.975,n-1)*se)
                test=ttest_rel(g.OPT.to_numpy(),g[rule].to_numpy(),alternative=alternative);p=float(test.pvalue)
                if not np.isfinite(p):p=1. if np.all(d==0) else (0. if alternative=='two-sided' or mean<0 else 1.)
                statistic=float(test.statistic) if np.isfinite(test.statistic) else (0. if mean==0 else math.copysign(float('inf'),mean))
                rows.append(dict(dataset=tag,budget=int(budget),method=method,comparison='OPT-minus-'+rule,n=n,
                                 difference=mean,se=se,lower=mean-half,upper=mean+half,t_statistic=statistic,p_raw=p))
    result=pd.DataFrame(rows);result['p_holm']=holm(result.p_raw)
    result['supports_OPT_lower']=(result.difference<0)&(result.p_holm<.05)
    return result

def analyze_saved_historical(formal_output, project_root=None):
    """Historical mean-test report; never called by the current default flow.

    These calculations do not establish full conditional MSE ordering. Use a
    separate copy of saved outputs when explicitly reproducing this history.
    """
    formal_output=Path(formal_output).resolve();project_root=Path(project_root or PACKAGE_ROOT).resolve()
    assert_writable_output(formal_output,project_root)
    config=read(formal_output/'protocol.json');mods=scientific_modules(project_root,formal_output.parent);analysis=mods['analyze']
    frame=analysis.load_records(formal_output)
    expected=sum(len(config[tag]['budgets'])*config[tag]['repetitions']*24 for tag in ['gdsc','year'])
    if len(frame)!=expected or frame.duplicated(['dataset','method','rule','budget','rep']).any():raise ValueError('Saved records are incomplete or duplicated.')
    if not np.isfinite(frame[analysis.METRICS]).all().all() or (frame.status!='complete').any():
        write(formal_output/'failure_summary.json',{'records':len(frame),'failed_records':int((frame.status!='complete').sum()),'all_records_retained':True,'finite_success_subset_not_reported_as_unconditional_mean':True})
        raise RuntimeError('All failures retained. Unconditional means cannot be replaced by a successful subset.')
    formal_mode=config.get('reproduction_mode','formal')=='formal'
    budgets={'gdsc':749,'year':5000} if formal_mode else {tag:config[tag]['budgets'][0] for tag in ['gdsc','year']}
    pairs=paired_comparisons(frame,budgets);old=paired_comparisons(frame,budgets,'less')
    old.to_csv(formal_output/'primary_comparisons_original_one_sided.csv',index=False)
    if formal_mode:
        # Reuse original figure data/formatting, while selecting current inference and N labels.
        import matplotlib.axes
        original_primary=analysis.primary;original_xlabel=matplotlib.axes.Axes.set_xlabel;original_ylabel=matplotlib.axes.Axes.set_ylabel
        analysis.primary=lambda _:pairs
        def xlabel(self,label,*args,**kwargs):return original_xlabel(self,label.replace('Draws r','Draws N'),*args,**kwargs)
        def ylabel(self,label,*args,**kwargs):return original_ylabel(self,label.replace('C/r','C/N'),*args,**kwargs)
        matplotlib.axes.Axes.set_xlabel=xlabel;matplotlib.axes.Axes.set_ylabel=ylabel
        try:analysis.main(SimpleNamespace(output=str(formal_output)))
        finally:
            analysis.primary=original_primary;matplotlib.axes.Axes.set_xlabel=original_xlabel;matplotlib.axes.Axes.set_ylabel=original_ylabel
    else:
        summary=analysis.summarize(frame);summary.to_csv(formal_output/'summary.csv',index=False)
        write(formal_output/'summary.json',{'completed':True,'records':len(frame),'role':'smoke only; no scientific efficacy claim','observed_step_bound_violations':int((~frame.step_bound_observed).sum())})
    pairs.to_csv(formal_output/'primary_comparisons.csv',index=False)
    pairs.to_csv(formal_output/'paired_comparisons_two_sided.csv',index=False)
    revision={'analysis':'two-sided paired t, one joint Holm over all 36 comparisons','conditional_on_fixed_data_and_parameters':True,
              'pointwise_intervals_not_simultaneous':True,'comparisons':len(pairs),'max_two_sided_holm_p':float(pairs.p_holm.max()),
              'original_one_sided_preserved_separately':True,'historical_exploration_not_adjusted':True,
              'role':'historical mean-based analysis; not current full-MSE evidence' if formal_mode else 'historical smoke analysis only'}
    write(formal_output/'inference_revision.json',revision)
    return revision


def analyze_saved(formal_output, project_root=None):
    """Current default: empirical summaries and descriptive figures, without tests."""
    from .empirical_v import analyze_records
    formal_output = Path(formal_output).resolve()
    project_root = Path(project_root or PACKAGE_ROOT).resolve()
    assert_writable_output(formal_output, project_root)
    config = read(formal_output/'protocol.json')
    if not read(formal_output/'execution.json').get('completed'):
        raise ValueError('Cannot report an incomplete experiment')
    # Fresh runs contain no earlier reports. Do not leave stale mean-test files
    # beside a current report or silently remove historical user artifacts.
    legacy = ['primary_comparisons.csv', 'paired_comparisons_two_sided.csv',
              'primary_comparisons_original_one_sided.csv', 'inference_revision.json']
    if any((formal_output/name).exists() for name in legacy):
        raise ValueError('Historical reports already exist; use run.py analyze with a new output directory')
    smoke = bool(config.get('reproduction_mode') == 'smoke' or config.get('run_mode') == 'smoke' or config.get('smoke_only'))
    summary = analyze_records(formal_output, config=config, smoke=smoke)
    summary.update(reproduction_mode='smoke' if smoke else 'formal',
                   role='reduced engineering check only; not paper results' if smoke else 'finite-repetition empirical reporting')
    write(formal_output/'summary.json', summary)
    return summary


def run(output, mode='smoke', workers=2, project_root=None, stable=False):
    project_root=Path(project_root or PACKAGE_ROOT).resolve();output=new_output(output,project_root)
    start=time.perf_counter()
    metadata=prepare_inputs(project_root,output/'inputs',mode)
    config=read(project_root/'Experiments'/EXPERIMENT/'formal_protocol.json')
    config.update(reproduction_mode=mode,reproduction_adapter='repro1026.exp5',support_stability_revision=stable)
    if mode=='smoke':
        for tag,budgets in [('gdsc',[24,48]),('year',[32,64])]:
            config[tag]['budgets']=budgets;config[tag]['repetitions']=3
            config[tag]['training_n']=metadata['datasets'][tag]['X'][0]
            config[tag]['test_n']=metadata['datasets'][tag]['E'][0]
            config[tag]['features']=metadata['datasets'][tag]['X'][1]
        config['sampling_seed']=202610270906
        config['smoke_parameter_override']='c=1 for every method; small implementation test only, not historical tuning or formal evidence'
    formal=output/'formal';formal.mkdir();(formal/'targets').mkdir();write(formal/'protocol.json',config)
    frozen={str(p.relative_to(project_root)).replace('\\','/'):sha(p) for p in (project_root/'Experiments'/EXPERIMENT/'src/native_exp5').glob('*.py')}
    frozen['repro1026/exp5.py']=sha(Path(__file__))
    if stable:
        from .v_stability import protocol
        stable_protocol=protocol()
        config['step_policy']=stable_protocol['step_policy']
        config['probability_policy']=stable_protocol['probability_policy']
        config['sampling_seed']=stable_protocol['formal_sampling_seed'] if mode=='formal' else stable_protocol['validation_sampling_seed']
        write(formal/'protocol.json',config)
        write(formal/'stability_protocol.json',stable_protocol)
        frozen['repro1026/v_stability.py']=sha(Path(__file__).with_name('v_stability.py'))
    write(formal/'frozen_sources.json',frozen)
    for relative in frozen:
        source=project_root/relative
        if source.is_file():
            destination=formal/'source_snapshot'/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    target_tasks=[(str(project_root),str(output),str(formal),tag,config,stable) for tag in ['gdsc','year']]
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(2,workers)) as pool:
        for _ in pool.map(_target_job,target_tasks):pass
    manifest={str(p.relative_to(formal)).replace('\\','/'):sha(p) for p in (formal/'targets').rglob('*') if p.is_file()}
    write(formal/'target_manifest.json',manifest)
    write(formal/'sampling_release.json',{'all_targets_derivatives_probabilities_frozen':True,'target_manifest_sha256':sha(formal/'target_manifest.json'),'protocol_sha256':sha(formal/'protocol.json'),'seconds_before_sampling':time.perf_counter()-start})
    tasks=[(str(project_root),str(output),(str(formal),tag,budget,rep,config['sampling_seed'])) for tag in ['gdsc','year'] for budget in config[tag]['budgets'] for rep in range(config[tag]['repetitions'])]
    total=0
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(_draw_job,tasks):total+=result[-1]
    write(formal/'execution.json',{'completed':True,'records':total,'tasks':len(tasks),'seconds':time.perf_counter()-start})
    reporting=analyze_saved(formal,project_root)
    result={'completed':True,'mode':mode,'stability_revision':stable,'input_preparation':metadata,'records':total,'reporting':reporting,
            'elapsed_seconds':time.perf_counter()-start,'source_archives_modified':False,'paper_formal_results_replaced':False}
    write(output/'reproduction.json',result);print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mode',choices=['smoke','formal'],default='smoke')
    parser.add_argument('--workers',type=int,default=2);parser.add_argument('--project-root',type=Path,default=PACKAGE_ROOT,help='Explicit alternate package root; no implicit access to the original workspace.')
    args=parser.parse_args()
    if args.workers<1:parser.error('--workers must be positive')
    run(args.output,args.mode,args.workers,args.project_root)

if __name__=='__main__':main()
