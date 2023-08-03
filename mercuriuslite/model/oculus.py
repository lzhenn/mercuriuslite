#!/usr/bin/env python3
"""specific module for IO"""

print_prefix='model.oculus>>'

from ..lib import utils, io
from . import zoo
import datetime, os, matplotlib
import numpy as np
matplotlib.use('Agg')

class Oculus:
    '''
    oculus caster: core class, model trainer, predictor
    '''
    def __init__(self, cfg):
        self.cfg=cfg
        self.model_name=cfg['PREDICTOR']['model_name']         
        self.Yfile=cfg['PREDICTOR']['Yfile']   
        self.Ytgt=cfg['PREDICTOR']['Ytgt']
        self.Xnames=cfg['PREDICTOR']['Xnames']

        if not(cfg['PREDICTOR']['train_start_time']=='0'):
            self.train_start_time=datetime.datetime.strptime(
                cfg['PREDICTOR']['train_start_time'], '%Y%m%d')
        else: 
            self.train_start_time='0'
        if not(cfg['PREDICTOR']['train_end_time']=='0'):
            self.train_end_time=datetime.datetime.strptime(
                cfg['PREDICTOR']['train_end_time'], '%Y%m%d')
        
        self.infer_start_time=cfg['PREDICTOR']['predict_start_time']
        if not(cfg['PREDICTOR']['predict_end_time']=='0'):
            self.infer_end_time=datetime.datetime.strptime(
                cfg['PREDICTOR']['predict_end_time'], '%Y%m%d')
        self.archive_flag=cfg['PREDICTOR'].getboolean('archive_flag')
        self.archive_dir=cfg['PREDICTOR']['archive_dir']               

        utils.write_log(f'{print_prefix}Mercurius.Oculus Initiation Done.')

    def train(self):
        utils.write_log(f'{print_prefix}Mercurius.Oculus.train()')
        self.X_train, self.Y_train, self.train_start_time, self.train_end_time =io.load_xy(
            self.Xnames, self.Yfile, self.Ytgt, 
            self.train_start_time, self.train_end_time)
        model_train = getattr(zoo, self.model_name)
        self.model=model_train(self)
        if self.archive_flag:
            model_archive = getattr(zoo, f'{self.model_name}_archive')
            model_archive(self)
    def predict(self):
        utils.write_log(f'{print_prefix}Mercurius.Oculus.predict()')
        model_predict = getattr(zoo, f'{self.model_name}_predict')
        self.determin, self.prob = model_predict(self)

    def fast_plot(self):
        import matplotlib.pyplot as plt
        nday_series=np.arange(self.determin.shape[0])
        plt.plot(
            nday_series, self.prob.T, 
            linestyle='-', linewidth=0.5, alpha=0.5,color='grey')
        plt.plot(
            nday_series, self.determin, label='Deterministic', 
            linestyle='-', linewidth=3, color='blue')
        plt.legend()
        plt.show()
        plt.savefig(os.path.join('./fig/', self.model_name+'.png'))