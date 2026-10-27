"""Every update and RK4 stage, with checkpointed exact discrete reverse derivatives.

The Householder basis is held fixed for the derivative of the dense recurrence.
It is an orthogonal coordinate change, never an eigenbasis or filter evaluation.
"""
from .common import *
from numba import njit

@njit(cache=True)
def matvec(diag,off,x):
    out=diag*x
    for j in range(len(off)):
        out[j]+=off[j]*x[j+1];out[j+1]+=off[j]*x[j]
    return out

@njit(cache=True)
def force(diag,off,rhs,s,code,t,eta):
    f=np.zeros_like(s)
    if code==2:f[0]=rhs-matvec(diag,off,s[0])
    else:
        f[0]=s[1];f[1]=(t if code==5 else 1.)*rhs-matvec(diag,off,s[0])
        if code==3:f[1]-=eta*s[1]
    return f

@njit(cache=True)
def transpose_force(diag,off,b,code,eta):
    result=np.zeros_like(b)
    for q in range(len(b)):
        if code==2:result[q,0]=-matvec(diag,off,b[q,0])
        else:
            result[q,0]=-matvec(diag,off,b[q,1]);result[q,1]=b[q,0]
            if code==3:result[q,1]-=eta*b[q,1]
    return result

@njit(cache=True)
def forward_block(diag,off,rhs,code,h,eta,start,count,state):
    s=state.copy();stages=np.zeros((count,4,len(rhs)))
    for jj in range(count):
        j=start+jj+1
        if code==1:
            stages[jj,0]=s[0];s[0]+=h*(rhs-matvec(diag,off,s[0]))
        elif code==4:
            z=s[0]+max(j-2,0)/j*(s[0]-s[1]);stages[jj,0]=z
            previous=s[0].copy();s[0]=z+h*(rhs-matvec(diag,off,z));s[1]=previous
        else:
            t=(j-1)*h
            k1=force(diag,off,rhs,s,code,t,eta);s2=s+h*k1/2
            k2=force(diag,off,rhs,s2,code,t+h/2,eta);s3=s+h*k2/2
            k3=force(diag,off,rhs,s3,code,t+h/2,eta);s4=s+h*k3
            k4=force(diag,off,rhs,s4,code,t+h,eta)
            stages[jj,0]=s[0];stages[jj,1]=s2[0];stages[jj,2]=s3[0];stages[jj,3]=s4[0]
            s+=h/6*(k1+2*k2+2*k3+k4)
    return s,stages

@njit(cache=True)
def reverse_block(diag,off,code,h,eta,start,count,ending):
    a=ending.copy();q=len(a);d=len(diag);weights=np.zeros((count,4,q,d));rhsgrad=np.zeros((q,d))
    for jj in range(count-1,-1,-1):
        j=start+jj+1;t=(j-1)*h
        if code==1 or code==4:
            for i in range(q):
                b=h*a[i,0];weights[jj,0,i]=b;rhsgrad[i]+=b
                z=a[i,0]-h*matvec(diag,off,a[i,0])
                if code==1:a[i,0]=z
                else:
                    momentum=max(j-2,0)/j
                    a[i,0]=(1+momentum)*z+a[i,1];a[i,1]=-momentum*z
        else:
            b1=h/6*a;b2=h/3*a;b3=h/3*a;b4=h/6*a;initial=a.copy()
            component=0 if code==2 else 1
            weights[jj,3]=b4[:,component];rhsgrad+=(t+h if code==5 else 1.)*b4[:,component]
            z=transpose_force(diag,off,b4,code,eta);initial+=z;b3+=h*z
            weights[jj,2]=b3[:,component];rhsgrad+=(t+h/2 if code==5 else 1.)*b3[:,component]
            z=transpose_force(diag,off,b3,code,eta);initial+=z;b2+=h/2*z
            weights[jj,1]=b2[:,component];rhsgrad+=(t+h/2 if code==5 else 1.)*b2[:,component]
            z=transpose_force(diag,off,b2,code,eta);initial+=z;b1+=h/2*z
            weights[jj,0]=b1[:,component];rhsgrad+=(t if code==5 else 1.)*b1[:,component]
            initial+=transpose_force(diag,off,b1,code,eta);a=initial
    return a,weights,rhsgrad

def reduce(M):
    H,Q=la.hessenberg(M,calc_q=True,check_finite=False)
    diag=np.diag(H).copy();off=np.diag(H,-1).copy()
    tri=np.diag(diag)+np.diag(off,1)+np.diag(off,-1)
    error=float(np.linalg.norm(Q@tri@Q.T-M,'fro')/max(1.,np.linalg.norm(M,'fro')))
    orth=float(np.linalg.norm(Q.T@Q-np.eye(len(M)),'fro'))
    assert error<3e-12 and orth<3e-12
    return diag,off,Q,error,orth

def parameters(method,alpha,L,refine=1):
    from scipy.optimize import brentq
    h=.9/L;eta=2*np.sqrt(alpha)
    if method=='Ridge':return dict(method=method,alpha=alpha,L=L,eta=eta,dt=0.,steps=0,T=0.)
    if method=='Landweber':k=math.ceil(1/(alpha*h));T=k*h
    elif method=='Nesterov':k=max(1,math.ceil((-3+math.sqrt(1+24/(alpha*h)))/2));T=k*h
    else:
        if method=='Showalter':T=1/alpha;maxdt=.9/L
        elif method=='HBF':T=brentq(lambda u:u-1+np.exp(-u)-4,4,6)/eta;maxdt=.2/max(np.sqrt(L),eta)
        else:T=np.sqrt(6/alpha);maxdt=.2/np.sqrt(L)
        k=math.ceil(T/maxdt)*refine;h=T/k
    return dict(method=method,alpha=float(alpha),L=float(L),eta=float(eta),dt=float(h),steps=int(k),T=float(T))

def trajectory(M,rhs,p,reduction=None,checkpoints=False,block=256):
    if p['method']=='Ridge':return la.solve(M+p['alpha']*np.eye(len(rhs)),rhs,assume_a='pos'),None
    reduction=reduce(M) if reduction is None else reduction
    diag,off,Q,_,_=reduction;c=np.ascontiguousarray(Q.T@rhs);state=np.zeros((2,len(c)))
    code={'Landweber':1,'Showalter':2,'HBF':3,'Nesterov':4,'SOAR':5}[p['method']]
    if not checkpoints:
        from .native_forward import execute
        return Q@execute(diag,off,c,code,p['steps'],p['dt'],p['T'],p['eta']),None
    saved=[]
    for start in range(0,p['steps'],block):
        if checkpoints:saved.append(state.copy())
        state,_=forward_block(diag,off,c,code,p['dt'],p['eta'],start,min(block,p['steps']-start),state)
    result=Q@(state[0]/p['T'] if code==5 else state[0])
    return result,dict(reduction=reduction,c=c,code=code,saved=saved,block=block) if checkpoints else None

def influences(M,rhs,p,Z,response,metric_factor,path=None,qbatch=8,block=256,progress=False):
    """Return J in coefficient-norm coordinates (R u for columns, beta for rows).

    Z columns are atoms; response=None for columns, row y otherwise.
    All parameters and Householder basis are held fixed when differentiating.
    """
    n,N=Z.shape;C=metric_factor
    target,record=trajectory(M,rhs,p,checkpoints=p['method']!='Ridge',block=block)
    J=np.lib.format.open_memmap(path,mode='w+',dtype='float64',shape=(len(C),N)) if path else np.empty((len(C),N))
    if p['method']=='Ridge':
        inverse_atoms=la.solve(M+p['alpha']*np.eye(n),Z,assume_a='pos')
        scalar=-Z.T@target if response is None else response-Z.T@target
        J[:]=(C@inverse_atoms)*scalar[None,:]
        if path:J.flush()
        return target,J
    diag,off,Q,_,_=record['reduction'];B=np.ascontiguousarray(Q.T@Z);qmat=Q.T@C.T
    if record['code']==5:qmat=qmat/p['T']
    starts=list(range(0,p['steps'],block))
    for qstart in range(0,len(C),qbatch):
        width=min(qbatch,len(C)-qstart);adj=np.zeros((width,2,n));adj[:,0]=qmat[:,qstart:qstart+width].T
        gradients=np.zeros((width,n,n));right=np.zeros((width,n))
        for ib in range(len(starts)-1,-1,-1):
            start=starts[ib];count=min(block,p['steps']-start)
            _,positions=forward_block(diag,off,record['c'],record['code'],p['dt'],p['eta'],start,count,record['saved'][ib])
            adj,weights,drhs=reverse_block(diag,off,record['code'],p['dt'],p['eta'],start,count,adj)
            stages=1 if record['code'] in [1,4] else 4
            U=positions[:,:stages].reshape(count*stages,n)
            for iq in range(width):gradients[iq]-=weights[:,:stages,iq].reshape(count*stages,n).T@U
            right+=drhs
        for iq in range(width):
            for left in range(0,N,4096):
                stop=min(N,left+4096);atoms=B[:,left:stop]
                values=np.sum(atoms*(gradients[iq]@atoms),axis=0)
                if response is not None:values+=(right[iq]@atoms)*response[left:stop]
                J[qstart+iq,left:stop]=values
        if path:J.flush()
        if progress:print('ADJOINT',p['method'],qstart+width,'/',len(C),'steps',p['steps'],flush=True)
    return target,J
