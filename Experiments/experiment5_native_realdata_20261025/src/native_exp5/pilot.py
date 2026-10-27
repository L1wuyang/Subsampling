"""Small dense recurrence, joint finite-difference and adjoint checks."""
from .common import *
from .kernel import parameters,trajectory,influences
from . import column_reference as col,row_reference as row
from scipy.integrate import solve_ivp

def main(args):
    if args.command=='freeze':
        protocol=read(HERE/'protocol_candidate.json');gate=read(HERE/'outputs/pilot_02/verification.json');assert gate['passed']
        assert read(HERE/'outputs/resource_audit_01/audit.json')['year']['finite_scores']
        sourcefiles=scientific_sources();expected=read(HERE/'outputs/pilot_02/frozen_sources.json')
        assert all(sha(HERE/k)==v for k,v in expected.items())
        assert not (HERE/'formal_protocol.json').exists()
        save(HERE/'formal_protocol.json',protocol);print('PROTOCOL_FROZEN',sha(HERE/'formal_protocol.json'),flush=True);return
    out=Path(args.output) if args.output else HERE/'outputs/pilot_01';out.mkdir(parents=True,exist_ok=False)
    guard();rng=np.random.default_rng(202610250905);checks=[]
    def add(name,error,tolerance):
        checks.append(dict(name=name,error=float(error),tolerance=tolerance));assert error<tolerance,(name,error)
    for direction in ['column','row']:
        X=rng.normal(size=(9,17)) if direction=='column' else rng.normal(size=(31,9));y=rng.normal(size=len(X))
        Z=X if direction=='column' else X.T;M=Z@Z.T;c=y if direction=='column' else X.T@y
        C=la.qr(X.T,mode='economic')[1] if direction=='column' else np.eye(len(M));L=32*np.linalg.norm(M,np.inf)
        for method in METHODS:
            p=parameters(method,np.trace(M)/len(M),L)
            actual,J=influences(M,c,p,Z,None if direction=='column' else y,C,block=37,qbatch=3)
            ref,Jref=(col.full(X,M,y,p) if direction=='column' else row.full(X,M,y,p))
            add(direction+'_'+method+'_dense_state',np.linalg.norm(actual-ref)/max(1,np.linalg.norm(ref)),2e-10)
            add(direction+'_'+method+'_all_native_tangents',np.linalg.norm(J-C@Jref)/max(1,np.linalg.norm(C@Jref)),3e-9)
            weights=rng.normal(size=Z.shape[1]);E=(Z*weights)@Z.T;dc=np.zeros_like(c) if direction=='column' else Z@(weights*y)
            h=1e-5;plus=trajectory(M+h*E,c+h*dc,p)[0];minus=trajectory(M-h*E,c-h*dc,p)[0]
            fd=C@(plus-minus)/(2*h);predicted=J@weights
            add(direction+'_'+method+'_joint_finite_difference',np.linalg.norm(fd-predicted)/max(1,np.linalg.norm(predicted)),2e-6)
            zero=trajectory(M,np.zeros_like(c),p)[0];add(direction+'_'+method+'_zero_response',np.linalg.norm(zero),1e-30)
            if method in ['Showalter','HBF','SOAR']:
                d=len(c)
                if method=='Showalter':
                    flow=solve_ivp(lambda t,u:c-M@u,[0,p['T']],np.zeros(d),method='DOP853',rtol=1e-11,atol=1e-13).y[:,-1]
                else:
                    def rhs(t,s):return np.r_[s[d:],(t*c if method=='SOAR' else c)-M@s[:d]-(p['eta']*s[d:] if method=='HBF' else 0)]
                    flow=solve_ivp(rhs,[0,p['T']],np.zeros(2*d),method='DOP853',rtol=1e-11,atol=1e-13).y[:d,-1]
                    if method=='SOAR':flow/=p['T']
                add(direction+'_'+method+'_independent_adaptive_flow',np.linalg.norm(actual-flow)/max(1,np.linalg.norm(flow)),3e-7)
                refined=trajectory(M,c,parameters(method,p['alpha'],L,2))[0]
                add(direction+'_'+method+'_doubled_grid',np.linalg.norm(actual-refined)/max(1,np.linalg.norm(refined)),3e-7)
    save(out/'verification.json',dict(passed=True,checks=checks,count=len(checks),no_spectral_shortcuts=True))
    save(out/'frozen_sources.json',{str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in scientific_sources()})
    print('PILOT_PASSED',len(checks),flush=True)

def scientific_sources():
    names=['__init__.py','common.py','data.py','kernel.py','native_forward.py','setup.py','pilot.py','formal.py','column_reference.py','row_reference.py','integrator_reference.py']
    return [HERE/'run.py',HERE/'requirements.txt',HERE/'protocol_candidate.json']+[HERE/'src/native_exp5'/n for n in names]
