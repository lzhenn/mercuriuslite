#!/usr/bin/env python3
"""model zoo"""

# ****************Available models*****************
#
# PlainHist: plain historical evolution
# SVPDF: single variable PDF
#
# ****************Available models*****************

# ---imports---
import numpy as np
from ..lib import utils, io, mathlib
from scipy.stats import linregress as linreg
# ---Module regime consts and variables---
print_prefix='model.zoo>>'

# ---Classes and Functions---

# ------------------------PlainHist------------------------
# plain historical evolution 
# return matR (nsample,nspan)

def plainhist(oculus):
    utils.write_log(f'{print_prefix}PlainHist Training...')    
    
    nspan=int(oculus.cfg['M_plainhist']['hist_span'])
    Y=oculus.Y_train
    nsample=Y.shape[0]-nspan+1
    matR=np.zeros((nsample,nspan))
    for i in range(nsample):
        matR[i,:] = Y[i:i+nspan]/Y[i]
    utils.write_log(f'{print_prefix}PlainHist Training Done!')    
    return matR
def plainhist_archive(oculus):
    io.savmatR(oculus)

def plainhist_predict(oculus):
    oculus.model, oculus.model_meta=io.load_model_npy(
        oculus.archive_dir, oculus.model_name, oculus.ticker)
    return oculus.model.mean(axis=0), oculus.model
# ------------------------PlainHist------------------------


# ------------------------SVPDF------------------------
# Single Variable PDF
def svpdf(oculus):
    utils.write_log(f'{print_prefix}svpdf Training...')    
    X, Y=oculus.X_train, oculus.Y_train
    
    # matR [nsample,0] -- Y, [nsample,1] -- X
    matR=np.hstack((Y.reshape(-1, 1), X))
    utils.write_log(f'{print_prefix}svpdf Training Done!') 
    return matR

def svpdf_archive(oculus):
    io.savmatR(oculus)

def svpdf_predict(oculus):
    oculus.prob_port=float(
        oculus.cfg['M_svpdf']['prob_portion'])
    oculus.model, oculus.model_meta = io.load_model_npy(oculus)
    determ, prob=mathlib.get_closest_samples(
        oculus.model,oculus.X_pred,oculus.prob_port)
    return determ, prob   
# ------------------------SVPDF------------------------


# ------------------------REGRESSION------------------------
def linregress(oculus):
    utils.write_log(f'{print_prefix}linregress Training...')    
    X, Y=oculus.X_train, oculus.Y_train
    res = linreg(X, y=Y)
    print(f"R-squared: {res.rvalue**2:.6f}")
    print(res.intercept, res.intercept_stderr)

def linregress_archive(oculus):
    io.savmatR(oculus)

def linregress_predict(oculus):
    return 0, 0
# ------------------------REGRESSION------------------------

# ----------COMMON FUNCTIONS----------

# ---Unit test---
if __name__ == '__main__':
    pass