#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
import os
import numpy as np
# ---Module regime consts and variables---
print_prefix='lib.math>>'


# ---Classes and Functions---
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
    maY[:k]=Y[:k]
    return maY

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
        conf=conf*prob/prob.sum()
    else:
        conf=conf*(1-prob)/(1-prob).sum()
    return conf
# ---Unit test---
if __name__ == '__main__':
    pass