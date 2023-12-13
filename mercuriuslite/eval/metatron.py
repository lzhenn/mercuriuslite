#!/usr/bin/env python3
"""Core Evaluator for models or strategies"""

print_prefix='eval.iustitia>>'
from ..lib import utils, io, painter
import os
import numpy as np

class Metatron:
    '''
    metatron evaluator: ticker metrics evaluator 
    '''
    def __init__(self,mercurius):
        self.cfg=mercurius.cfg
        self.tickers=self.cfg['INSPECTOR']['ana_tickers'].replace(' ','').split(',')
        self.metric=self.cfg['INSPECTOR']['metric']
        self.method_name=self.cfg['INSPECTOR']['method']
        self.hist={}
                
        self.eval_start_time=utils.parse_intime(
            self.cfg['INSPECTOR']['inspect_start_time'])     
        self.eval_end_time=utils.parse_intime(
            self.cfg['INSPECTOR']['inspect_end_time'])
        
        for ticker in self.tickers:
            self.hist[ticker]=io.load_hist(mercurius.ltm_dir,ticker)
        
        dateseries=self.hist[self.tickers[0]].index
        if self.eval_start_time != '0':
            idx_start=dateseries.searchsorted(self.eval_start_time)
        else:
            idx_start=0
        if self.eval_end_time != '0':
            idx_end=dateseries.searchsorted(self.eval_end_time)
        else:
            idx_end=-1
        self.dateseries=dateseries[idx_start:idx_end]
        for tgt in self.tickers:
            self.hist[tgt]=self.hist[tgt].loc[self.dateseries]
    
        if self.cfg['INSPECTOR'].getboolean('trim_flag'):
            self.hist, lenhist=utils.trim_hist(self.hist) 
        self.metricval=np.zeros((lenhist,len(self.tickers)))
    
    def analyze(self):
        for idx,ticker in enumerate(self.tickers):
            self.metricval[:,idx]= getattr(utils, 'cal_'+self.metric.lower())(self.hist[ticker])
        self.method = getattr(self, self.method_name)
        self.method() 
    def histogram(self):
        '''
        Use bayes test to determine the confidence level
        '''
        utils.write_log(f'{print_prefix}Mercurius.metatron.histogram()...')
           
        fig_fn=os.path.join(
            self.cfg['POSTPROCESS']['fig_path'],
            '.'.join([self.method_name,self.metric,'png']))
        xnames=self.tickers
        painter.draw_histograms(self.metricval, xnames, fig_fn)
    
    def corr_heatmap(self):
        utils.write_log(f'{print_prefix}Mercurius.metatron.corr_heatmap()...')
        corr_matrix = np.corrcoef(self.metricval, rowvar=False)
        fig_fn=os.path.join(
            self.cfg['POSTPROCESS']['fig_path'],
            '.'.join([self.method_name,self.metric,'png']))
        xnames=self.tickers
        for idx,ticker in enumerate(xnames):
            self.change=self.hist[ticker]['Close'][-1]/self.hist[ticker]['Close'][0]-1
            xnames[idx]=xnames[idx]+'('+utils.fmt_value(self.change,vtype='pct')+')'
        painter.draw_corr_heatmap(corr_matrix, xnames, fig_fn)
