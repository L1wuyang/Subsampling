"""Training-only preprocessing; immutable raw files and historical split indices."""
from .common import *
import pandas as pd
import gzip

def normalize(train,test,y,ey):
    mean=train.mean(0);scale=train.std(0);keep=scale>1e-12;ym=float(y.mean())
    assert np.isfinite(train).all() and np.isfinite(test).all()
    return ((train[:,keep]-mean[keep])/scale[keep],(test[:,keep]-mean[keep])/scale[keep],
            y-ym,ey-ym,dict(mean=mean,scale=scale,keep=keep,response_mean=ym))

def prepare(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    raw=ROOT/'Data/real_data_20261016/raw'
    old=ROOT/'Experiments/real_data_pilot_20261017/outputs/pilot_03'
    expression=raw/'gdsc/expression_release_6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz'
    response=raw/'gdsc/response_release_8.4/GDSC2_fitted_dose_response_24Jul22.csv'
    year=raw/'yearpredictionmsd/yearpredictionmsd/YearPredictionMSD.txt'
    for p in [expression,response,year]:assert p.is_file()
    with gzip.open(expression,'rt',encoding='utf8') as stream:ids=list(map(int,stream.readline().rstrip().split('\t')[1:]))
    table=pd.read_csv(expression,sep='\t',compression='gzip');genes=table.iloc[:,0].astype(str).to_numpy()
    unique_genes=~pd.Series(genes).duplicated(keep=False).to_numpy()
    counts=pd.Series(ids).value_counts();index={v:j for j,v in enumerate(ids) if counts[v]==1}
    pairs=pd.read_csv(old/'gdsc_selected_pairs.csv').sort_values('COSMIC_ID')
    rr=pd.read_csv(response);rr=rr[(rr.DRUG_ID==1862)&rr.COSMIC_ID.isin(pairs.COSMIC_ID)].sort_values('COSMIC_ID')
    assert np.array_equal(rr.COSMIC_ID.to_numpy(),pairs.COSMIC_ID.to_numpy())
    assert np.array_equal(rr.LN_IC50.to_numpy(),pairs.LN_IC50.to_numpy())
    X=table.iloc[:,1:].to_numpy(dtype=float)[unique_genes][:,[index[int(v)] for v in pairs.COSMIC_ID]].T.copy()
    y=pairs.LN_IC50.to_numpy();assert X.shape==(937,17737)
    cache=ROOT/'Experiments/real_data_other_methods_20261019/outputs/scaled_01/input_cache'
    assert np.array_equal(X,np.load(cache/'X.npy',mmap_mode='r')) and np.array_equal(y,np.load(cache/'y.npy'))
    prep=np.load(old/'column_preprocessing_and_split.npz');lookup={int(v):j for j,v in enumerate(pairs.COSMIC_ID)}
    tr=np.array([lookup[int(v)] for v in prep['train_ids']]);te=np.array([lookup[int(v)] for v in prep['test_ids']])
    assert len(tr)==749 and len(te)==188 and not set(tr)&set(te)
    T,E,ty,ey,pp=normalize(X[tr],X[te],y[tr],y[te])
    folder=out/'gdsc';folder.mkdir()
    for name,value in [('X',T),('E',E),('y',ty),('ey',ey)]:np.save(folder/(name+'.npy'),value)
    np.savez_compressed(folder/'preprocessing.npz',**pp,train=tr,test=te,train_ids=pairs.COSMIC_ID.to_numpy()[tr],test_ids=pairs.COSMIC_ID.to_numpy()[te],genes=genes[unique_genes])
    del table,X,T,E
    arr=pd.read_csv(year,header=None).to_numpy(dtype=float);assert arr.shape==(515345,91)
    T,E,ty,ey,pp=normalize(arr[:463715,1:],arr[463715:,1:],arr[:463715,0],arr[463715:,0])
    folder=out/'year';folder.mkdir()
    for name,value in [('X',T),('E',E),('y',ty),('ey',ey)]:np.save(folder/(name+'.npy'),value)
    np.savez_compressed(folder/'preprocessing.npz',**pp,train=np.arange(463715),test=np.arange(463715,515345))
    sources=[expression,response,year,old/'gdsc_selected_pairs.csv',old/'column_preprocessing_and_split.npz']
    save(out/'source_manifest.json',{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sources})
    report={}
    for tag,direction in [('gdsc','column'),('year','row')]:
        d=load(out,tag);X=d['X'];Z=X if direction=='column' else X.T;A=Z@Z.T
        report[tag]=dict(direction=direction,n=len(X),p=X.shape[1],test_n=len(d['E']),trace=float(np.trace(A)),
            infinity_norm=float(np.linalg.norm(A,np.inf)),max_atom_squared_norm=float(np.sum(Z*Z,axis=0).max()),
            original_step=.01/(Z.shape[1]*float(np.sum(Z*Z,axis=0).max())))
    save(out/'preflight.json',report)
    save(out/'data_manifest.json',{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='data_manifest.json'})
    print('DATA_PREPARED',report,flush=True)

def load(out,tag):
    folder=Path(out)/tag
    return dict(tag=tag,direction='column' if tag=='gdsc' else 'row',**{n:np.load(folder/(n+'.npy'),mmap_mode='r') for n in ['X','E','y','ey']})
