"""Every native update, in an orthogonal tridiagonal coordinate system.

Householder reduction is not eigendecomposition: eigenvectors/eigenvalues
are never computed. All prescribed LW/Nesterov steps and RK4 stages run.
No fastmath, analytic residual, polynomial powers, or early stopping.
"""
from .common import np,la
from numba import njit

@njit(cache=True)
def tri_force(diag,off,u,rhs,mult,out):
    n=len(u)
    for i in range(n):
        val=diag[i]*u[i]
        if i:val+=off[i-1]*u[i-1]
        if i+1<n:val+=off[i]*u[i+1]
        out[i]=mult*rhs[i]-val

@njit(cache=True)
def execute(diag,off,rhs,code,k,h,T,eta):
    n=len(rhs);u=np.zeros(n);v=np.zeros(n);tmp=np.zeros(n)
    a=np.zeros(n);b=np.zeros(n);c=np.zeros(n);d=np.zeros(n)
    av=np.zeros(n);bv=np.zeros(n);cv=np.zeros(n);dv=np.zeros(n)
    for j in range(1,k+1):
        if code==1:
            tri_force(diag,off,u,rhs,1.,a)
            for i in range(n):u[i]+=h*a[i]
        elif code==4:
            momentum=max(j-2,0)/j
            for i in range(n):tmp[i]=u[i]+momentum*(u[i]-v[i])
            tri_force(diag,off,tmp,rhs,1.,a)
            for i in range(n):v[i]=u[i];u[i]=tmp[i]+h*a[i]
        elif code==2:
            tri_force(diag,off,u,rhs,1.,a)
            for i in range(n):tmp[i]=u[i]+h*a[i]/2
            tri_force(diag,off,tmp,rhs,1.,b)
            for i in range(n):tmp[i]=u[i]+h*b[i]/2
            tri_force(diag,off,tmp,rhs,1.,c)
            for i in range(n):tmp[i]=u[i]+h*c[i]
            tri_force(diag,off,tmp,rhs,1.,d)
            for i in range(n):u[i]+=h/6*(a[i]+2*b[i]+2*c[i]+d[i])
        else:
            t=(j-1)*h
            tri_force(diag,off,u,rhs,t if code==5 else 1.,av)
            for i in range(n):
                if code==3:av[i]-=eta*v[i]
                a[i]=v[i];b[i]=v[i]+h*av[i]/2;tmp[i]=u[i]+h*a[i]/2
            tri_force(diag,off,tmp,rhs,t+h/2 if code==5 else 1.,bv)
            for i in range(n):
                if code==3:bv[i]-=eta*b[i]
                c[i]=v[i]+h*bv[i]/2;tmp[i]=u[i]+h*b[i]/2
            tri_force(diag,off,tmp,rhs,t+h/2 if code==5 else 1.,cv)
            for i in range(n):
                if code==3:cv[i]-=eta*c[i]
                d[i]=v[i]+h*cv[i];tmp[i]=u[i]+h*c[i]
            tri_force(diag,off,tmp,rhs,t+h if code==5 else 1.,dv)
            for i in range(n):
                if code==3:dv[i]-=eta*d[i]
                u[i]+=h/6*(a[i]+2*b[i]+2*c[i]+d[i])
                v[i]+=h/6*(av[i]+2*bv[i]+2*cv[i]+dv[i])
    if code==5:
        for i in range(n):u[i]/=T
    return u

def reduce(M):
    H,Q=la.hessenberg(M,calc_q=True,check_finite=False)
    diag=np.diag(H).copy();off=np.diag(H,-1).copy()
    tri=np.diag(diag)+np.diag(off,1)+np.diag(off,-1)
    err=float(np.linalg.norm(Q@tri@Q.T-M,'fro')/max(1.,np.linalg.norm(M,'fro')))
    orth=float(np.linalg.norm(Q.T@Q-np.eye(len(M)),'fro'))
    assert err<3e-13 and orth<3e-13
    return diag,off,Q,err,orth

def solve(M,rhs,p,reduced=None):
    if p['method']=='Ridge':return la.solve(M+p['alpha']*np.eye(len(rhs)),rhs,assume_a='pos')
    diag,off,Q,_,_=reduce(M) if reduced is None else reduced
    code={'Landweber':1,'Showalter':2,'HBF':3,'Nesterov':4,'SOAR':5}[p['method']]
    u=execute(diag,off,np.ascontiguousarray(Q.T@rhs),code,p['steps'],p['dt'],p['T'],p['eta'])
    return Q@u
