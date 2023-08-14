#!/usr/bin/env python3
"""Core Evaluator for models or strategies"""

print_prefix='lib.iustitia>>'
from ..lib import utils, io, mathlib, const
from ..model import zoo
import numpy as np

class Iustitia:
    '''
    iustitia evaluator: core class, model and strategy evaluator 
    '''
    def __init__(self, oculus, cfg):
        self.cfg=cfg
        self.oculus=oculus
        self.eval_name=cfg['EVALUATOR']['eval_name']
        self.eval_start_time=utils.parse_intime(
            self.cfg['EVALUATOR']['eval_start_time'])     
        self.eval_end_time=utils.parse_intime(
            self.cfg['EVALUATOR']['eval_end_time'])
    

    def bayes_test(self):
        '''
        Use bayes test to determine the confidence level
        '''
        utils.write_log(f'{print_prefix}Mercurius.Iustitia.bayes_test()...')
        oculus=self.oculus
        ylead=oculus.Ylead
        X_test, Y_test, whole_span =io.load_xy(
            oculus.Xfile, oculus.Xnames, oculus.Yfile, oculus.Ytgt, ylead)
        idx_start=whole_span.searchsorted(self.eval_start_time)
        if self.eval_end_time == '0':
            idx_end=whole_span.shape[0]
        else:
            idx_end=whole_span.searchsorted(self.eval_end_time)
        oculus._load_baseline()
        model_predict = getattr(zoo, f'{oculus.model_name}_predict')
        
        test_span=whole_span[idx_start:idx_end]
        X_test, Y_test=X_test[idx_start:idx_end],Y_test[idx_start:idx_end]

        winning=np.zeros(2)
        if ylead>10:
            strt_range=(np.arange(5)*ylead/5).astype(int)
        else :
            strt_range=np.arange(1)
        for strt_idx in strt_range:
            belief=mathlib.init_belief(2)
            for idx, date_tick in enumerate(test_span[strt_idx::ylead]):
                abs_id=idx*ylead+strt_idx
                oculus.X_pred=X_test[abs_id]
                oculus.determin, oculus.prob = model_predict(oculus)
                y, ybase=oculus.prob[:,0], oculus.baseline

                winning[0]=mathlib.win_prob(y)
                winning[1]=mathlib.win_prob(ybase)
                belief=mathlib.bayes_update(belief, winning, Y_test[abs_id]>0)
            print(belief)
            
    
def strategy_eval(track):
    table_dic={}
    track_start=track.iloc[0]
    track_end=track.iloc[-1]
    
    table_dic['Backtest Start:']=track.index[0].strftime("%Y-%m-%d")
    table_dic['Backtest End:']=track.index[-1].strftime("%Y-%m-%d")
    val=(track.index[-1]-track.index[0]).days+1
    total_days=val
    table_dic['Total Test Duration']=f'{val} days'
    
    val=utils.fmt_value(track_end['accu_fund'])
    table_dic['Cumulative Funding']=val
    
    val=utils.fmt_value(track_end['total_value'])
    table_dic['Cumulative Value']=val
    
    twr=track_end['accum_return']-1
    val=utils.fmt_value(twr,vtype='pct')
    table_dic['Time-Weighted Return (TWR)']=val
    
    val=utils.fmt_value(track_end['fund_change'],vtype='pct')
    table_dic['Average Rate of Return (ARR)']=val 
    
    cagr=mathlib.cagr(twr,total_days)
    val=utils.fmt_value(cagr,vtype='pct')
    table_dic['Compound Annual Growth Rate (CAGR)']=val
    
    drawdown=track['drawdown'].max()
    val=utils.fmt_value(-drawdown,vtype='pct')
    table_dic['Max Drawdown']=val
   
    val=utils.fmt_value(cagr/drawdown,vtype='f')
    table_dic['MAR']=val
    
    val=utils.fmt_value(
        track_end['norisk_total_value']/track_end['accu_fund']-1,vtype='pct')
    table_dic['No Risk ARR']=val 
    return table_dic