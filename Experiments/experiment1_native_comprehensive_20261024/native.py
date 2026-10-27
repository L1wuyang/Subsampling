"""Fixed-parameter actual recurrences, forward tangents and numerical flows.

Parameters are held fixed when M is perturbed. SOAR s=.5 uses w=t*u,
w''+M*w=t*y, integrated from the nonsingular zero initial conditions.
No spectral evaluation, polynomial power shortcut or event stopping.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
import numpy as np
import scipy.linalg as sla
from scipy.optimize import brentq
METHODS=['Ridge','Landweber','Showalter','HBF','Nesterov','SOAR']
RULES=['UNI','NORM','LEV','OPT']

def guard():
    def blocked(*a,**k):raise AssertionError('Forbidden spectral shortcut')
    for name in ('eig','eigh','eigvals','eigvalsh','svd','matrix_power'):setattr(np.linalg,name,blocked)
    for name in ('eig','eigh','eigvals','eigvalsh','svd','svdvals','expm','funm','fractional_matrix_power'):setattr(sla,name,blocked)

def optimal(scores,epsilon):
    floor=epsilon/len(scores)
    if scores.max()<=1e-30:return np.full(len(scores),1/len(scores))
    z=brentq(lambda c:np.maximum(floor,c*scores).sum()-1,0,2/scores.sum(),xtol=1e-14)
    pi=np.maximum(floor,z*scores)
    assert abs(pi.sum()-1)<1e-10
    return pi

def baselines(X,epsilon):
    H=X@X.T; norms=np.sum(X*X,axis=0);p=X.shape[1]
    lev=np.maximum(np.sum(X*sla.solve(H,X,assume_a='pos'),axis=0),0)
    return H,dict(UNI=np.full(p,1/p),NORM=(1-epsilon)*norms/norms.sum()+epsilon/p,
                  LEV=(1-epsilon)*lev/lev.sum()+epsilon/p)

def parameters(method,alpha,L,refine=1):
    eta=2*np.sqrt(alpha)
    if method=='Ridge':return dict(method=method,alpha=alpha,eta=eta,steps=0,dt=0.,T=0.)
    if method in ('Landweber','Nesterov'):
        h=.9/L
        k=int(np.ceil(1/(alpha*h))) if method=='Landweber' else max(1,int(np.ceil((-3+np.sqrt(1+24/(alpha*h)))/2)))
        return dict(method=method,alpha=alpha,eta=eta,steps=k,dt=h,T=k*h)
    if method=='Showalter':T=1/alpha; maxdt=.9/L
    elif method=='HBF':
        z=brentq(lambda z:z-1+np.exp(-z)-4,4,6);T=z/eta;maxdt=.2/max(np.sqrt(L),eta)
    else:T=np.sqrt(6/alpha);maxdt=.2/np.sqrt(L)
    k=int(np.ceil(T/maxdt))*refine
    return dict(method=method,alpha=alpha,eta=eta,steps=k,dt=T/k,T=T)

def integrate(param,force,shape):
    method=param['method'];h=param['dt'];eta=param['eta'];k=param['steps']
    u=np.zeros(shape);v=np.zeros_like(u)
    for j in range(1,k+1):
        if method=='Landweber':u=u+h*force(u,1.)
        elif method=='Nesterov':
            z=u+max(j-2,0)/j*(u-v);un=z+h*force(z,1.);v,u=u,un
        elif method=='Showalter':
            a=force(u,1.);b=force(u+h*a/2,1.);c=force(u+h*b/2,1.);d=force(u+h*c,1.)
            u=u+h/6*(a+2*b+2*c+d)
        else:
            t=(j-1)*h
            def acc(z,q,tt):return force(z,tt if method=='SOAR' else 1.)-(eta*q if method=='HBF' else 0.)
            a=v;av=acc(u,v,t)
            b=v+h*av/2;bv=acc(u+h*a/2,b,t+h/2)
            c=v+h*bv/2;cv=acc(u+h*b/2,c,t+h/2)
            d=v+h*cv;dv=acc(u+h*c,d,t+h)
            u=u+h/6*(a+2*b+2*c+d);v=v+h/6*(av+2*bv+2*cv+dv)
    if method=='SOAR':u=u/param['T']
    return u

def full(X,H,y,param):
    n,p=X.shape
    if param['method']=='Ridge':
        A=H+param['alpha']*np.eye(n);u=sla.solve(A,y,assume_a='pos')
        J=-sla.solve(A,X,assume_a='pos')*(X.T@u)[None,:]
        return u,J
    def force(W,t):
        Z=-H@W;Z[:,0]+=t*y;Z[:,1:]-=X*(X.T@W[:,0])[None,:];return Z
    W=integrate(param,force,(n,p+1));return W[:,0],W[:,1:]

def batch(Ms,y,param):
    if param['method']=='Ridge':return np.linalg.solve(Ms+param['alpha']*np.eye(len(y)),np.broadcast_to(y,(len(Ms),len(y)))[...,None])[...,0]
    def force(U,t):return t*y-np.einsum('bij,bj->bi',Ms,U,optimize=False)
    return integrate(param,force,(len(Ms),len(y)))

def setup(X,y,c=1.,epsilon=.01,method_subset=None):
    H,ps=baselines(X,epsilon);norms=np.sum(X*X,axis=0);alpha=c*np.trace(H)/len(y)
    L=max(float(np.max(norms/pi)) for pi in ps.values())
    history=[];methods=method_subset or METHODS
    # At most eight doubling trials, then a universal floor bound. No sketch
    # uniforms are generated or consulted during this deterministic setup.
    for trial in range(10):
        models={};required=L
        for method in methods:
            param=parameters(method,alpha,L);u,J=full(X,H,y,param)
            scores=np.sqrt(np.maximum(np.sum(J*(H@J),axis=0),0));pi=optimal(scores,epsilon)
            models[method]=dict(param=param,u=u,J=J,scores=scores,pi=pi)
            if method!='Ridge':required=max(required,float(np.max(norms/pi)))
        history.append(dict(trial=trial,L=L,required=required))
        if required<=L*(1+1e-12):return H,ps,models,history
        L=max(2*L,1.01*required) if trial<7 else len(norms)/epsilon*norms.max()
    raise RuntimeError('Deterministic atom bound construction did not converge')

def matrices(X,pi,uniforms):
    cdf=np.cumsum(pi);cdf[-1]=1.;out=[]
    for row in uniforms:
        ix=np.searchsorted(cdf,row,side='right');counts=np.bincount(ix,minlength=X.shape[1]);nz=np.flatnonzero(counts)
        Z=X[:,nz]*np.sqrt(counts[nz]/(len(row)*pi[nz]));out.append(Z@Z.T)
    return np.array(out)
