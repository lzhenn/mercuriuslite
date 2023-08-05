#!/usr/bin/env python3
"""Core Model"""

print_prefix='model.oculus>>'

from ..lib import utils, io, painter
from . import zoo
import datetime, os
import numpy as np

class Oculus:
    '''
    oculus caster: core class, model trainer, predictor
    '''
    def __init__(self, cfg):
        self.cfg=cfg
        self.model_name=cfg['PREDICTOR']['model_name']
        self.Xfile=cfg['PREDICTOR']['Xfile']         
        self.Yfile=cfg['PREDICTOR']['Yfile']
        self.Ytgt_str=cfg['PREDICTOR']['Ytgt'] 
        self.Ytgt, self.Ylead=utils.parse_lead(cfg['PREDICTOR']['Ytgt'])
        self.Xnames=cfg['PREDICTOR']['autoXnames']

        # Train
        self.train_start_time=utils.parse_intime(
            cfg['PREDICTOR']['train_start_time'])
        self.train_end_time=utils.parse_intime(
            cfg['PREDICTOR']['train_end_time'])
        
        self.archive_flag=cfg['PREDICTOR'].getboolean('archive_flag')
        self.archive_dir=cfg['PREDICTOR']['archive_dir']               

        # Predict       
        self.pred_init_time=datetime.datetime.strptime(
            cfg['PREDICTOR']['predict_init_time'])
        self.pred_init_time=utils.parse_intime(
                cfg['PREDICTOR']['predict_init_time'])

        utils.write_log(f'{print_prefix}Mercurius.Oculus Initiation Done.')

    def train(self):
        utils.write_log(f'{print_prefix}Mercurius.Oculus.train()')
        self.X_train, self.Y_train, self.train_start_time, self.train_end_time =io.load_xy(
            self.Xfile, self.Xnames, self.Yfile, self.Ytgt, self.Ylead,
            self.train_start_time, self.train_end_time)
        
        model_train = getattr(zoo, self.model_name)
        self.model=model_train(self)
        if self.archive_flag:
            model_archive = getattr(zoo, f'{self.model_name}_archive')
            model_archive(self)

    def predict(self):
        utils.write_log(f'{print_prefix}Mercurius.Oculus.predict()')
        hist_Y, _, self.pred_init_time =io.load_y(
            self.Yfile, self.Ytgt, 
            end_time=self.pred_init_time, call_from='predict')
        X_pred_series=io.load_x(
            hist_Y, self.Xfile, self.Xnames, 
            end_time=self.pred_init_time, call_from='predict')
        self.X_pred=X_pred_series[-1]
        model_predict = getattr(zoo, f'{self.model_name}_predict')
        self.determin, self.prob = model_predict(self)
        self._load_baseline()
        
    def _load_baseline(self):
        '''
        Load baseline (histplain) model for comparison
        '''
        baseline=io.load_model_npy(self, baseline=True)
        self.baseline=baseline[:,self.Ylead]-1

    def bayes_test(self):
        '''
        Use bayes test to determine the confidence level
        '''
        utils.write_log(f'{print_prefix}Mercurius.Oculus.bayes_test()...')
        test_start_time=utils.parse_intime(
            self.cfg['PREDICTOR']['test_start_time'])     
        test_end_time=utils.parse_intime(
            self.cfg['PREDICTOR']['test_end_time'])
        
        self._load_baseline()
        
        hist_Y, _, self.pred_init_time =io.load_y(
            self.Yfile, self.Ytgt, 
            end_time=test_start_time, call_from='predict')
        X_pred_series=io.load_x(
            hist_Y, self.Xfile, self.Xnames, 
            end_time=test_start_time, call_from='predict')
        self.X_pred=X_pred_series[-1]
        model_predict = getattr(zoo, f'{self.model_name}_predict')
        self.determin, self.prob = model_predict(self)
        exit()


    def fast_plot(self):
        painter.fast_plot(self)