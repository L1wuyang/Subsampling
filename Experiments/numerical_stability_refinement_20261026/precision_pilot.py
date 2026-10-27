"""Selected same-draw high-precision Nesterov replay. Never overwrites archives."""
from pathlib import Path
import os,json,time,argparse,hashlib
for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']:os.environ[k]='1'
import numpy as np
import mpmath as mp
from dd_native import weighted_gram,nesterov,add,mul,product
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ARCHIVE=ROOT/'Experiments/experiment4_native_comprehensive_20261025/outputs/formal_01'

def matrix(hi,lo):
    if hi.ndim==1:return mp.matrix([mp.mpf(float(a))+mp.mpf(float(b)) for a,b in zip(hi,lo)])
    return mp.matrix([[mp.mpf(float(hi[i,j]))+mp.mpf(float(lo[i,j])) for j in range(hi.shape[1])] for i in range(hi.shape[0])])

def split(values):
    a=list(values);hi=np.array([float(v) for v in a]);lo=np.array([float(v-mp.mpf(float(v))) for v in a]);return hi,lo

def tridiagonal(M):
    A=M.copy();n=M.rows;Q=mp.eye(n)
    for k in range(n-2):
        v=mp.matrix([A[i,k] for i in range(k+1,n)]);length=mp.sqrt(mp.fdot(v,v))
        if length==0:continue
        alpha=-mp.sign(v[0])*length if v[0] else -length
        v[0]-=alpha;v/=mp.sqrt(mp.fdot(v,v))
        block=A[k+1:n,k+1:n];a=block*v;w=2*(a-mp.fdot(v,a)*v)
        A[k+1:n,k+1:n]=block-v*w.T-w*v.T
        qb=Q[:,k+1:n];Q[:,k+1:n]=qb-2*(qb*v)*v.T
        for i in range(k+1,n):A[i,k]=alpha if i==k+1 else 0;A[k,i]=A[i,k]
    tri=mp.diag([A[i,i] for i in range(n)])
    for i in range(n-1):tri[i,i+1]=A[i+1,i];tri[i+1,i]=A[i+1,i]
    residual=mp.norm(Q*tri*Q.T-M)/max(1,mp.norm(M))
    assert residual<mp.mpf('1e-65'),residual
    return Q,tri,residual

def arithmetic_checks():
    rng=np.random.default_rng(2026102602);worst=mp.mpf(0)
    for _ in range(1000):
        a,b=rng.normal(size=2);ah,al=product(a,b)
        assert mp.mpf(float(ah))+mp.mpf(float(al))==mp.mpf(float(a))*mp.mpf(float(b))
        a2,b2=rng.normal(size=2)*1e-16
        ah,al=add(a,a2,b,b2);exact=mp.mpf(float(a))+mp.mpf(float(a2))+mp.mpf(float(b))+mp.mpf(float(b2))
        worst=max(worst,abs((mp.mpf(float(ah))+mp.mpf(float(al)))-exact))
        ah,al=mul(a,a2,b,b2);exact=(mp.mpf(float(a))+mp.mpf(float(a2)))*(mp.mpf(float(b))+mp.mpf(float(b2)))
        worst=max(worst,abs((mp.mpf(float(ah))+mp.mpf(float(al)))-exact))
    assert worst<mp.mpf('1e-29'),worst
    return mp.nstr(worst,12)

def run(direction,budget,out):
    out.mkdir(parents=True,exist_ok=False);mp.mp.dps=80;start=time.perf_counter()
    report={'direction':direction,'budget':budget,'rep':0,'precision':'double-double (~106 significant binary bits), 80-decimal setup/LS','longdouble_bits':int(np.finfo(np.longdouble).nmant),'arithmetic_check_max_abs_error':arithmetic_checks()}
    folder=ARCHIVE/f'{direction}_01';rawfile=folder/'main'/f'r{budget}_c0000.npz'
    with np.load(folder/'data.npz') as data:X=data['X'];y=data['y']
    with np.load(rawfile) as raw:counts=raw['counts'][0];old=raw['Nesterov_state'][0];oldls=raw['ls_state'][0]
    setup=json.loads((folder/'setup.json').read_text());h=setup['h'];a=setup['a']
    steps=max(1,int(np.ceil(2*np.log(budget)/(-np.log1p(-h*a))-1)))
    column=direction=='column';Mh,Ml,ch,cl=weighted_gram(X,y,counts,budget,column)
    M=matrix(Mh,Ml);rhs=matrix(ch,cl)
    print('HIGH_PRECISION_GRAM_READY',direction,budget,flush=True)
    Q,T,residual=tridiagonal(M);c=Q.T*rhs
    dh,dl=split([T[i,i] for i in range(len(rhs))]);oh,ol=split([T[i+1,i] for i in range(len(rhs)-1)]);rh,rl=split(c)
    ls=mp.lu_solve(M,rhs);lsres=mp.norm(M*ls-rhs)/max(1,mp.norm(rhs));assert lsres<mp.mpf('1e-65')
    # Independent arbitrary-precision check of literal early recurrence.
    prefix=min(200,steps);u=mp.matrix(len(rhs),1);v=u.copy();hm=mp.mpf(h)
    for j in range(1,prefix+1):
        beta=mp.mpf(max(j-2,0))/j;z=u+beta*(u-v);v,u=u,z+hm*(c-T*z)
    ph,pl=nesterov(dh,dl,oh,ol,rh,rl,h,prefix,True);prefixerr=mp.norm(matrix(ph,pl)-u)/max(1,mp.norm(u))
    assert prefixerr<mp.mpf('1e-27'),prefixerr
    tick=time.perf_counter();nesterov(dh,dl,oh,ol,rh,rl,h,min(10000,steps),True);benchmark=time.perf_counter()-tick
    print('REPLAY_BENCHMARK',direction,'steps',steps,'estimated_seconds',benchmark*steps/min(10000,steps),flush=True)
    modes={}
    for rational,label in [(True,'rational_momentum'),(False,'binary64_momentum')]:
        tick=time.perf_counter();uh,ul=nesterov(dh,dl,oh,ol,rh,rl,h,steps,rational);state=Q*matrix(uh,ul)
        coeff=mp.matrix(X.T.tolist())*state if column else state
        coeffls=mp.matrix(X.T.tolist())*ls if column else ls
        oldcoef=mp.matrix(X.T.tolist())*mp.matrix(old.tolist()) if column else mp.matrix(old.tolist())
        oldlscoef=mp.matrix(X.T.tolist())*mp.matrix(oldls.tolist()) if column else mp.matrix(oldls.tolist())
        gap=mp.norm(coeff-coeffls);change=mp.norm(coeff-oldcoef);lschange=mp.norm(coeffls-oldlscoef)
        modes[label]={'steps':steps,'executed_all_steps':True,'seconds':time.perf_counter()-tick,'gap_norm':mp.nstr(gap,35),'scaled_squared_gap':mp.nstr(budget*gap**2,35),'coefficient_change_from_archived':mp.nstr(change,35),'LS_change_from_archived':mp.nstr(lschange,35),'old_gap_norm_recomputed_mp':mp.nstr(mp.norm(oldcoef-oldlscoef),35)}
        (out/(label+'_state.json')).write_text(json.dumps([mp.nstr(x,70) for x in state],indent=2)+'\n',encoding='utf8')
        print('HIGH_PRECISION_REPLAY_COMPLETE',direction,label,modes[label],flush=True)
    report.update(modes=modes,householder_relative_residual=mp.nstr(residual,12),LS_relative_residual=mp.nstr(lsres,12),prefix_vs_80_decimal_error=mp.nstr(prefixerr,12),seconds=time.perf_counter()-start,input_note='Exact binary64 original X/y promoted; uniform weights recomputed as rational counts*N/budget. Gram accumulated in double-double. This refines all arithmetic, not just the last subtraction. Same saved counts/h/step count; no spectral trajectory.',limitation='One 106-bit full-trajectory tier; 80-decimal reference verifies setup and first 200 steps, not the complete trajectory. No rigorous end-to-end rounding-error certificate.')
    (out/'precision_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--direction',choices=['column','row'],required=True);parser.add_argument('--budget',type=int,default=38400);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.direction,args.budget,args.output)
