"""Three-component floating expansions for an independent ~159-bit replay.

All Nesterov updates run. Error-free binary64 sums/products are distilled
into three components; fourth-component terms are rounded away. No fastmath.
"""
import numpy as np
from numba import njit
from dd_native import two_sum,product

@njit(cache=True,fastmath=False)
def renorm(a,b,c):
    b,c=two_sum(b,c);a,b=two_sum(a,b);b,c=two_sum(b,c);a,b=two_sum(a,b)
    return a,b,c

@njit(cache=True,fastmath=False)
def accum(a,b,c,x):
    a,e=two_sum(a,x);b,e=two_sum(b,e);c,e=two_sum(c,e)
    return renorm(a,b,c)

@njit(cache=True,fastmath=False)
def add(a,b,c,d,e,f):
    a,b,c=accum(a,b,c,d);a,b,c=accum(a,b,c,e)
    return accum(a,b,c,f)

@njit(cache=True,fastmath=False)
def mul(a,b,c,d,e,f):
    aa=(a,b,c);bb=(d,e,f);s,t,u=0.,0.,0.
    for degree in range(5):
        for i in range(3):
            j=degree-i
            if j<0 or j>2:continue
            p,q=product(aa[i],bb[j]);s,t,u=accum(s,t,u,p);s,t,u=accum(s,t,u,q)
    return s,t,u

@njit(cache=True,fastmath=False)
def ratio(a,b):
    r,s,t=a,0.,0.;x,y,z=0.,0.,0.
    for j in range(3):
        q=r/b;x,y,z=accum(x,y,z,q);p,e=product(q,b);r,s,t=add(r,s,t,-p,-e,0.)
    return x,y,z

@njit(cache=True,fastmath=False)
def weighted_gram(X,y,counts,budget,column):
    Z=X if column else X.T;n,N=Z.shape;M=np.zeros((n,n,3));rhs=np.zeros((n,3))
    for atom in range(N):
        if counts[atom]==0:continue
        wh,wm,wl=ratio(float(N*counts[atom]),float(budget))
        for i in range(n):
            zh,zm,zl=mul(wh,wm,wl,Z[i,atom],0.,0.)
            if not column:
                th,tm,tl=mul(zh,zm,zl,y[atom],0.,0.)
                rhs[i,0],rhs[i,1],rhs[i,2]=add(rhs[i,0],rhs[i,1],rhs[i,2],th,tm,tl)
            for j in range(i,n):
                th,tm,tl=mul(zh,zm,zl,Z[j,atom],0.,0.)
                M[i,j,0],M[i,j,1],M[i,j,2]=add(M[i,j,0],M[i,j,1],M[i,j,2],th,tm,tl)
    for i in range(n):
        for j in range(i):M[i,j]=M[j,i]
    if column:
        for i in range(n):rhs[i,0]=y[i]
    return M,rhs

@njit(cache=True,fastmath=False)
def nesterov(diag,off,rhs,h,steps):
    n=len(rhs);u=np.zeros((n,3));v=np.zeros_like(u);z=np.zeros_like(u);new=np.zeros_like(u)
    for j in range(1,steps+1):
        bh,bm,bl=ratio(float(max(j-2,0)),float(j))
        for i in range(n):
            dh,dm,dl=add(u[i,0],u[i,1],u[i,2],-v[i,0],-v[i,1],-v[i,2]);dh,dm,dl=mul(bh,bm,bl,dh,dm,dl)
            z[i,0],z[i,1],z[i,2]=add(u[i,0],u[i,1],u[i,2],dh,dm,dl)
        for i in range(n):
            fh,fm,fl=mul(diag[i,0],diag[i,1],diag[i,2],z[i,0],z[i,1],z[i,2])
            if i:
                th,tm,tl=mul(off[i-1,0],off[i-1,1],off[i-1,2],z[i-1,0],z[i-1,1],z[i-1,2]);fh,fm,fl=add(fh,fm,fl,th,tm,tl)
            if i+1<n:
                th,tm,tl=mul(off[i,0],off[i,1],off[i,2],z[i+1,0],z[i+1,1],z[i+1,2]);fh,fm,fl=add(fh,fm,fl,th,tm,tl)
            fh,fm,fl=add(rhs[i,0],rhs[i,1],rhs[i,2],-fh,-fm,-fl);fh,fm,fl=mul(h,0.,0.,fh,fm,fl)
            new[i,0],new[i,1],new[i,2]=add(z[i,0],z[i,1],z[i,2],fh,fm,fl)
        for i in range(n):
            for k in range(3):v[i,k]=u[i,k];u[i,k]=new[i,k]
    return u
