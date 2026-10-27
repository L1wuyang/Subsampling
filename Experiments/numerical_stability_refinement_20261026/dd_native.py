"""Double-double arithmetic and literal Nesterov steps for precision diagnosis.

No eigendecomposition, spectral residual, matrix power, convergence shortcut,
or early stopping. Numba fastmath is explicitly disabled. Dekker products
assume the moderate normal-range operands present in these diagnostics.
"""
import os
from pathlib import Path
os.environ['NUMBA_CACHE_DIR']=str(Path(__file__).resolve().parent/'outputs/numba_cache')
import numpy as np
from numba import njit

@njit(cache=True,fastmath=False)
def two_sum(a,b):
    s=a+b;z=s-a;e=(a-(s-z))+(b-z)
    return s,e

@njit(cache=True,fastmath=False)
def product(a,b):
    p=a*b;c=134217729.*a;ah=c-(c-a);al=a-ah
    c=134217729.*b;bh=c-(c-b);bl=b-bh
    e=((ah*bh-p)+ah*bl+al*bh)+al*bl
    return p,e

@njit(cache=True,fastmath=False)
def add(ah,al,bh,bl):
    s,e=two_sum(ah,bh);t,f=two_sum(al,bl);e=e+t
    s,e=two_sum(s,e);e=e+f
    return two_sum(s,e)

@njit(cache=True,fastmath=False)
def mul(ah,al,bh,bl):
    p,e=product(ah,bh);e=e+(ah*bl+al*bh);e=e+al*bl
    return two_sum(p,e)

@njit(cache=True,fastmath=False)
def ratio(a,b):
    q=a/b;ph,pl=product(q,b);rh,rl=add(a,0.,-ph,-pl)
    return two_sum(q,(rh+rl)/b)

@njit(cache=True,fastmath=False)
def weighted_gram(X,y,counts,budget,column):
    Z=X if column else X.T;n,N=Z.shape
    Mh=np.zeros((n,n));Ml=np.zeros_like(Mh);ch=np.zeros(n);cl=np.zeros(n)
    for atom in range(N):
        if counts[atom]==0:continue
        wh,wl=ratio(float(N*counts[atom]),float(budget))
        for i in range(n):
            zh,zl=mul(wh,wl,Z[i,atom],0.)
            if not column:
                th,tl=mul(zh,zl,y[atom],0.);ch[i],cl[i]=add(ch[i],cl[i],th,tl)
            for j in range(i,n):
                th,tl=mul(zh,zl,Z[j,atom],0.)
                Mh[i,j],Ml[i,j]=add(Mh[i,j],Ml[i,j],th,tl)
    for i in range(n):
        for j in range(i):Mh[i,j]=Mh[j,i];Ml[i,j]=Ml[j,i]
    if column:
        for i in range(n):ch[i]=y[i]
    return Mh,Ml,ch,cl

@njit(cache=True,fastmath=False)
def nesterov(diagh,diagl,offh,offl,ch,cl,h,steps,rational=True):
    n=len(ch);uh=np.zeros(n);ul=np.zeros(n);vh=np.zeros(n);vl=np.zeros(n)
    zh=np.zeros(n);zl=np.zeros(n);nh=np.zeros(n);nl=np.zeros(n)
    for j in range(1,steps+1):
        if rational:bh,bl=ratio(float(max(j-2,0)),float(j))
        else:bh=float(max(j-2,0))/j;bl=0.
        for i in range(n):
            dh,dl=add(uh[i],ul[i],-vh[i],-vl[i]);dh,dl=mul(bh,bl,dh,dl)
            zh[i],zl[i]=add(uh[i],ul[i],dh,dl)
        for i in range(n):
            fh,fl=mul(diagh[i],diagl[i],zh[i],zl[i])
            if i:
                th,tl=mul(offh[i-1],offl[i-1],zh[i-1],zl[i-1]);fh,fl=add(fh,fl,th,tl)
            if i+1<n:
                th,tl=mul(offh[i],offl[i],zh[i+1],zl[i+1]);fh,fl=add(fh,fl,th,tl)
            fh,fl=add(ch[i],cl[i],-fh,-fl);fh,fl=mul(h,0.,fh,fl)
            nh[i],nl[i]=add(zh[i],zl[i],fh,fl)
        for i in range(n):vh[i]=uh[i];vl[i]=ul[i];uh[i]=nh[i];ul[i]=nl[i]
    return uh,ul
