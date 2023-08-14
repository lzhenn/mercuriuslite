#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
import os
from . import const
import numpy as np
# ---Module regime consts and variables---
print_prefix='lib.math>>'


# ---Classes and Functions---

def ar2dr(x):
    x=x+1
    return x**(1.0/const.DAYS_PER_YEAR)

def cagr(r, ndays):
    return (1+r)**(const.DAYS_PER_YEAR/ndays)-1
def get_closest_samples(matR, x, nsub=0.05):
    n_samples = matR.shape[0]
    n_subsamples = int(nsub * n_samples)
    indices = np.argsort(np.abs(matR[:,1] - x))[:n_subsamples]
    prob=matR[indices,:]
    determ=[prob.mean(axis=0)[0], x]
    return determ, prob

def ma(Y, k):
    maY=np.zeros(len(Y))
    for j in range(len(Y)-k+1):
        maY[j+k-1]=Y[j:j+k].sum()/k
    for j in range(0,k):
        maY[j]=Y[:j+1].sum()/(j+1)
    return maY
def stdma(Y, maY, k):
    stdY=np.zeros(len(Y))
    for j in range(len(Y)-k+1):
        series=Y[j:j+k]-maY[j+k-1]
        stdY[j+k-1]=np.std(series)
    for j in range(0,k):
        series=Y[:j+1]-maY[j]
        stdY[j]=np.std(series)
    return stdY+1e-10

def bollpct(Y, k):
    '''
    return relative position of bollinger band
    -1: bottom of band, 1: top of band
    '''
    boll=np.zeros(len(Y))
    maY=ma(Y, k)
    stdY=stdma(Y,maY,k)
    boll=(Y-(maY-2.0*stdY))/(4.0*stdY)
    return boll

def init_belief(n):
    belief=np.ones(n)/n
    return belief

def kelly(p, wf, lf):
    '''
    return kelly factor
    p:  prob of winning
    wf: winning gain fraction, lf: losing fraction
    '''
    return p/lf - (1-p)/wf

def odds(Y, r0=0.0):
    '''
    return odds given no risk r0

    '''
    wf = (Y[Y>r0]).mean()
    lf = (Y[Y<=r0]).mean()
    return wf, lf 

def win_prob(Y, r0=0.0):
    '''
    return winning probability given no risk r0
    '''
    return (Y>r0).sum()/len(Y)

def bayes_update(conf, prob, flag):
    '''
    update conf(n) according to flag
    '''
    if flag==1:
        conf=conf*prob/(conf*prob).sum()
    else:
        conf=conf*(1-prob)/(conf*(1-prob)).sum()
    return conf
# ---Unit test---
if __name__ == '__main__':
    pass