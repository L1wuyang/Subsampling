"""Data, deterministic parameter paths, QR LS and saved-output metrics."""
import os
for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS']:os.environ[key]='1'
from pathlib import Path
import hashlib,json,time,csv,math
import numpy as np
import scipy.linalg as la
from scipy.optimize import brentq
HERE=Path(__file__).resolve().parents[2]
ROOT=HERE.parents[1]
METHODS=['Ridge','Landweber','Showalter','HBF','Nesterov','SOAR']
DIRECTIONS=['column','row']
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def write(path,rows):
    if not rows:return
    with Path(path).open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def scientific():
    return [HERE/'run.py',HERE/'requirements.txt']+[HERE/'src/native_exp4'/n for n in ['__init__.py','common.py','kernel.py','formal.py','pilot.py','column_reference.py','integrator_reference.py','row_reference.py']]
def guard():
    def blocked(*a,**k):raise AssertionError('Forbidden spectral trajectory shortcut')
    for name in ['eig','eigh','eigvals','eigvalsh','svd','matrix_power']:setattr(np.linalg,name,blocked)
    for name in ['eig','eigh','eigvals','eigvalsh','svd','svdvals','expm','funm','fractional_matrix_power']:setattr(la,name,blocked)
def dataset(seed,direction,did,d=60,N=1200,zero=False):
    rng=np.random.default_rng(np.random.SeedSequence([seed,DIRECTIONS.index(direction),did]))
    if direction=='column':
        G=rng.normal(size=(d,N));s=np.exp(rng.normal(size=N));s=np.minimum(s,np.quantile(s,.98));s/=np.sqrt(np.mean(s*s))
        X=G*s/np.sqrt(d);beta=rng.normal(size=N);beta/=np.linalg.norm(beta)
        covariance=s*s/d;mask=np.zeros(N,dtype=bool)
    else:
        mask=np.zeros(N,dtype=bool);mask[rng.choice(N,round(.03*N),replace=False)]=True
        G=.25*rng.normal(size=(N,d))+8*rng.normal(size=(N,d))*mask[:,None]
        scale=np.sqrt(d/np.sum(G*G));X=scale*G;beta=rng.normal(size=d);beta/=np.linalg.norm(X@beta)/np.sqrt(N)
        covariance=np.full(d,scale**2*(.25**2+mask.mean()*8**2))
    y=X@beta+.5*rng.normal(size=len(X))
    if zero:y=np.zeros_like(y)
    return dict(X=X,y=y,beta0=beta,covariance=covariance,spike_mask=mask,direction=direction)
def atoms(data):return data['X'] if data['direction']=='column' else data['X'].T
def full_setup(data):
    Z=atoms(data);A=Z@Z.T;d=len(A);I=np.eye(d)
    la.cholesky(A,lower=True)
    lo=0.;hi=float(np.trace(A)/d)
    for _ in range(48):
        mid=(lo+hi)/2
        try:la.cholesky(A-mid*I,lower=True,check_finite=False);lo=mid
        except la.LinAlgError:hi=mid
    a=lo/2;b=float(np.linalg.norm(A,ord=np.inf)+a)
    L=float(Z.shape[1]*np.max(np.sum(Z*Z,axis=0)));h=.9/max(b,L)
    assert a>0 and a<hi and h*b<1
    return dict(a=a,b=b,L=L,h=h,lambda_min_bracket=[lo,hi],bound_method='48 Cholesky SPD bisections; infinity-norm upper bound; no eigendecomposition')
def parameters(setup,r,method,refine=1):
    a=setup['a'];L=max(setup['b'],setup['L']);h=setup['h'];eta=2*np.sqrt(a)
    p=dict(method=method,a=a,L=L,eta=float(eta),alpha=0.,T=0.,dt=0.,steps=0,budget=int(r),residual_bound=float(1/r))
    if method=='Ridge':p['alpha']=float(a/(r-1));return p
    if method=='Landweber':k=math.ceil(math.log(r)/(-math.log1p(-h*a)));dt=h;T=k*h
    elif method=='Nesterov':k=max(1,math.ceil(2*math.log(r)/(-math.log1p(-h*a))-1));dt=h;T=k*h
    else:
        if method=='Showalter':T=math.log(r)/a;maxdt=.9/L
        elif method=='HBF':
            u=brentq(lambda z:math.log1p(z)-z+math.log(r),0,4*math.log(r)+10);T=u/np.sqrt(a);maxdt=.2/max(np.sqrt(L),eta)
        else:T=r/np.sqrt(a);maxdt=.2/np.sqrt(L)
        k=math.ceil(T/maxdt)*refine;dt=T/k
    p.update(steps=int(k),dt=float(dt),T=float(T));return p
def counts_for(seed,direction,did,r,reps,arm=0,N=1200):
    rng=np.random.default_rng(np.random.SeedSequence([seed,DIRECTIONS.index(direction),did,r,arm]))
    return rng.multinomial(r,np.full(N,1/N),size=reps).astype(np.int32)
def sketch(data,counts):
    ix=np.flatnonzero(counts);weights=counts[ix]*(len(counts)/counts.sum());Z=atoms(data)[:,ix]*np.sqrt(weights)
    M=Z@Z.T
    rhs=data['y'].copy() if data['direction']=='column' else Z@(data['y'][ix]*np.sqrt(weights))
    return M,rhs,Z,ix,weights
def ls_reference(data,rhs,Z,ix,weights):
    # LAPACK GELSY is complete orthogonal factorization with pivoted QR.
    # The sampling-atom threshold is 1e-12; no normal-equation rank cutoff.
    if data['direction']=='column':
        v,_,rank,_=la.lstsq(Z,rhs,cond=1e-12,lapack_driver='gelsy')
        state,_,rank2,_=la.lstsq(Z.T,v,cond=1e-12,lapack_driver='gelsy')
        assert rank==rank2
    else:
        state,_,rank,_=la.lstsq(Z.T,data['y'][ix]*np.sqrt(weights),cond=1e-12,lapack_driver='gelsy')
    return state,int(rank)
def beta(data,state):return data['X'].T@state if data['direction']=='column' else state
def metrics(data,state,ls,r):
    B=beta(data,state);BL=beta(data,ls);gap=B-BL;norm=float(BL@BL);delta=B-data['beta0'];signal=data['X']@data['beta0']
    future=float(np.sum(delta**2*data['covariance']));absolute=float(gap@gap)
    floor=float(64*np.finfo(float).eps*max(1.,np.linalg.norm(B),np.linalg.norm(BL)))
    return dict(scaled_squared_gap=r*absolute,absolute_squared_gap=absolute,relative_squared_gap=absolute/norm if norm>1e-24 else np.nan,
                gap_norm=float(np.sqrt(absolute)),arithmetic_resolution_floor=floor,resolution_limited=bool(np.sqrt(absolute)<=floor),
                true_coef_rel_sq=float(delta@delta/(data['beta0']@data['beta0'])),design_signal_rel_sq=float(np.sum((data['X']@delta)**2)/(signal@signal)),
                population_signal_rel_sq=future/float(np.sum(data['beta0']**2*data['covariance'])),population_response_mse=future+.25,
                residual_norm=float(np.linalg.norm(data['y']-data['X']@B)))
