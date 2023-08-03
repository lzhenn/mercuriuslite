#!/usr/bin/env python3
"""model zoo"""
# ---imports---
import os
import numpy as np
import pandas as pd
from ..lib import utils, cfgparser
# ---Module regime consts and variables---
print_prefix='model.zoo>>'

# ---Classes and Functions---

# ------------------------PlainHist------------------------
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
    archive_dir=oculus.archive_dir
    np.save(os.path.join(archive_dir,'plainhist.npy'), oculus.model)
    cfgparser.write_cfg(oculus.cfg, os.path.join(archive_dir,'plainhist.ini'))
    utils.write_log(f'{print_prefix}PlainHist Archive Done!')

def plainhist_predict(oculus):
    utils.write_log(f'{print_prefix}PlainHist Predict...')
    if not(hasattr(oculus,'model')):
        archive_dir=oculus.archive_dir
        oculus.model = np.load(
            os.path.join(archive_dir,'plainhist.npy'))
    return oculus.model.mean(axis=0), oculus.model


# ------------------------PlainHist------------------------
# ---Unit test---
if __name__ == '__main__':
    pass