"""Complete-data outputs and derivatives precede all formal sampling streams."""
from .common import *
from .kernel import parameters,influences,trajectory
from .data import load
from scipy.optimize import brentq

HISTORIC_C=dict(gdsc={m:1. for m in METHODS},year=dict(Ridge=1e-6,Landweber=.001,Showalter=.001,HBF=.001,Nesterov=1e-5,SOAR=1e-5))

def basis(data):
    X=data['X'];column=data['direction']=='column';Z=X if column else X.T;M=Z@Z.T
    if column:
        Q,R,piv=la.qr(X.T,mode='economic',pivoting=True);C=R[:,np.argsort(piv)]
    else:
        Q,R,piv=la.qr(X,mode='economic',pivoting=True);C=np.eye(X.shape[1])
    diagonal=np.abs(np.diag(R));rank=int(np.count_nonzero(diagonal>1e-10*diagonal.max()))
    lev=np.sum(Q[:,:rank]**2,axis=1);del Q
    norms=np.sum(Z*Z,axis=0);N=Z.shape[1]
    ps=dict(UNI=np.full(N,1/N),NORM=.99*norms/norms.sum()+.01/N,LEV=.99*lev/lev.sum()+.01/N)
    if column:ps['NORM']=ps['UNI'].copy()
    rhs=data['y'] if column else X.T@data['y']
    return M,rhs,C,Z,ps,rank

def optimum(scores):
    N=len(scores);floor=.01/N
    if scores.max()<1e-30:return np.full(N,1/N)
    f=lambda t:np.maximum(floor,t*scores).sum()-1
    z=brentq(f,0,2/scores.sum(),xtol=1e-15,rtol=1e-14)
    pi=np.maximum(floor,z*scores);pi/=pi.sum()
    assert pi.min()>=floor*(1-1e-12)
    return pi

def make(out,tag,config):
    folder=Path(out)/tag;folder.mkdir(parents=True,exist_ok=False);data=load(HERE/'inputs',tag)
    M,rhs,C,Z,ps,rank=basis(data);norms=np.sum(Z*Z,axis=0)
    L=float(config['step_infinity_factor']*np.linalg.norm(M,np.inf))
    np.save(folder/'M.npy',M);np.save(folder/'C.npy',C)
    for name,pi in ps.items():np.save(folder/(name+'_probability.npy'),pi)
    report=dict(tag=tag,direction=data['direction'],n=len(data['X']),p=data['X'].shape[1],rank=rank,L=L,
        step_bound='32 times complete-data infinity norm; not a support-wide sampled-matrix bound. No adaptation to a formal draw.',models={})
    for method in METHODS:
        start=time.perf_counter();alpha=HISTORIC_C[tag][method]*np.trace(M)/len(M);p=parameters(method,alpha,L)
        dest=folder/method;dest.mkdir();target,J=influences(M,rhs,p,Z,None if tag=='gdsc' else data['y'],C,dest/'influences.npy',qbatch=config['adjoint_batch'],block=config['checkpoint_block'],progress=True)
        squared=np.sum(J*J,axis=0);scores=np.sqrt(np.maximum(squared,0));pi=optimum(scores);sumJ=np.sum(J,axis=1)
        probabilities={**ps,'OPT':pi};den=float(np.dot(C@target,C@target));constants={}
        for rule,prob in probabilities.items():
            value=float(np.sum(squared/prob)-np.dot(sumJ,sumJ));assert value>=-1e-8*max(1,np.sum(squared/prob))
            constants[rule]=max(value,0)/den if den>1e-24 else None
        assert constants['OPT']<=min(constants.values())*(1+1e-8)
        np.save(dest/'target.npy',target);np.save(dest/'OPT_probability.npy',pi);np.save(dest/'scores.npy',scores)
        if tag=='gdsc':prediction=data['E']@data['X'].T@target;design=M@target
        else:prediction=data['E']@target;design=data['X']@target
        full=dict(response_test_mse=float(np.mean((prediction-data['ey'])**2)),response_test_rmse=float(np.sqrt(np.mean((prediction-data['ey'])**2))),coefficient_norm_squared=den)
        np.save(dest/'test_prediction.npy',prediction);np.save(dest/'design_prediction.npy',design)
        save(dest/'parameters.json',p);save(dest/'summary.json',dict(c=HISTORIC_C[tag][method],full=full,constants=constants,seconds=time.perf_counter()-start,
            minimum_opt_probability=float(pi.min()),maximum_atom_to_probability=float(np.max(norms/pi))))
        report['models'][method]=dict(parameters=p,**read(dest/'summary.json'))
        print('FULL_TARGET_COMPLETE',tag,method,report['models'][method]['seconds'],flush=True)
        del J
    save(folder/'setup.json',report)
    return report
