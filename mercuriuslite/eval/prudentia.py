#!/usr/bin/env python3
"""Core Evaluator for models or strategies"""

print_prefix='eval.prudentia>>'
from ..lib import utils, io, mathlib, painter
from ..strategy import indicators
import numpy as np
import os
class Prudentia:
    '''
    prudentia evaluator: core class, single target strategy vector evaluator 
    '''
    def __init__(self, mercurius):
        self.cfg=mercurius.cfg
        self.strategy_name=self.cfg['EVALUATOR']['strategy_name']
        self.strategy=getattr(indicators, self.strategy_name)
        self.tickers=self.cfg['EVALUATOR']['tickers'].replace(' ','').split(',')
        
        portions=self.cfg['EVALUATOR']['portions'].replace(' ','').split(',')
        portions=[float(port) for port in portions][0:len(self.tickers)]
        portions=np.asarray(portions)
        self.portions=portions/portions.sum()
        
        self.ltm_dir=mercurius.ltm_dir
        self.baseticker=mercurius.baseticker
        self.paras=self.cfg['EVALUATOR']['paras'].replace(' ','').split('/')
        
        self.eval_start_time=utils.parse_intime(
            self.cfg['EVALUATOR']['eval_start_time'])     
        self.eval_end_time=utils.parse_intime(
            self.cfg['EVALUATOR']['eval_end_time'])
    

        
        self._load_hist()
        self._init_portfolio()

    def _load_hist(self):
        self.hist={}
        for tgt in self.tickers:
            utils.write_log(f'{print_prefix}load {tgt}')
            self.hist[tgt]=io.load_hist(self.ltm_dir, tgt)

        self.hist, _ =utils.trim_hist(self.hist) 
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
        self.basehist=io.load_hist(self.ltm_dir, self.baseticker, dateseries=self.dateseries) 
    def _init_portfolio(self):
        # build portfolio track
        dateseries=self.dateseries
        self.track = utils.init_track(dateseries, self.tickers)
 
    def judge(self):
        track=self.track
        
        accu_fund=10000
        
        track['accu_fund']=accu_fund*np.ones(len(track))
        track['norisk_total_value']=track['accu_fund']
        for idx,tgt in enumerate(self.tickers):
            idx_start=self.hist[tgt].index.searchsorted(track.index[0])
            print(self.hist[tgt],self.paras[idx].replace(' ','').split(','),idx_start)
            
            track['action']=self.strategy(
                self.hist[tgt], self.paras[idx].replace(' ','').split(','),idx_start)[:-1]
            cash2use=accu_fund*self.portions[idx]
            track=vector_eval(track,self.hist[tgt],tgt,cash2use=cash2use) 
        track['total_value']=track['cash']+track['port_value']
        dr_vec=1+np.diff(
            track['total_value'].values,prepend=accu_fund)/np.concatenate(([accu_fund],track['total_value'].values[:-1]))
        track['daily_return']=dr_vec
        track['drawdown'] = (
            track['total_value'].cummax() - track['total_value']) / track['total_value'].cummax()
        track=track_inspect(track)
    
        
        track=baseline_inspect(track,self.basehist) 
        eval_table=strategy_eval(track)
        print(painter.table_print(eval_table))
        fig_fn=os.path.join(
            self.cfg['POSTPROCESS']['fig_path'],
            '.'.join([self.strategy_name,'eval','png'])) 
        painter.draw_perform_fig(
            track, self.tickers, fig_fn)
    

def vector_eval(track, hist, tgt, price_tgt='Close', cash2use=10000):
    len_vec=len(track)
    hist=hist.loc[track.index]
    # all in numpy!
    price_vec=hist[price_tgt].values
    value_vec,share_vec,cash_vec=np.zeros(len_vec), np.zeros(len_vec), np.zeros(len_vec)
    cash_vec[0]=cash2use
    act_vec=track['action'].values
    if act_vec[0]==1:
            share_vec[0]+=cash2use/price_vec[0]
            value_vec[0]=cash2use
            cash_vec[0]=0
    for idx in np.arange(1, len_vec):
        if act_vec[idx]==0:
            share_vec[idx]=share_vec[idx-1]
            value_vec[idx]=share_vec[idx]*price_vec[idx]
            cash_vec[idx]=cash_vec[idx-1]
        elif act_vec[idx]==1:
            share_vec[idx]+=cash_vec[idx-1]/price_vec[idx]
            value_vec[idx]=cash_vec[idx-1]
            cash_vec[idx]=0
        elif act_vec[idx]==-1 and value_vec[idx-1]>0:
            share_vec[idx]=0
            value_vec[idx]=0
            cash_vec[idx]=cash_vec[idx-1]+value_vec[idx-1]
            cash2use=value_vec[idx-1]
        else:
            cash_vec[idx]=cash_vec[idx-1]
    track[tgt+'_value']=value_vec
    track[tgt+'_share']=share_vec
    track['cash']+=cash_vec
    track['port_value']+=value_vec
    #print(track.loc[(track['action']==1 )| (track['action']==-1)])
    return track

def track_inspect(track):
    # Total gain relative to accu in/out fund 
    track['fund_change']=(track['total_value']-track['accu_fund'])/track['accu_fund']
    track['daily_return']=np.log(track['daily_return'])
    track['accum_return']=np.exp(track['daily_return'].cumsum())
    track['daily_net_return']=np.log(track['daily_net_return'])
    track['accum_net_return']=np.exp(track['daily_net_return'].cumsum())
    track['drawdown'] = (
        track['accum_return'].cummax() - track['accum_return']) / track['accum_return'].cummax()
    track['net_drawdown'] = (
        track['accum_net_return'].cummax() - track['accum_net_return']) / track['accum_net_return'].cummax()
    return track

def baseline_inspect(track, basehist):
    basehist=basehist['Close']
    # baseline return
    track['baseline_return']=track['accum_return']
    base_value=basehist.loc[track.index[0]]
    track['baseline_return']=basehist[track.index[0]:track.index[-1]]/base_value
    track['baseline_drawdown'] = (
        track['baseline_return'].cummax() - track['baseline_return']) / track['baseline_return'].cummax()

    return track

def strategy_eval(track):
    table_dic={}
    track_end=track.iloc[-1]
    
    table_dic['Backtest Start:']=track.index[0].strftime("%Y-%m-%d")
    table_dic['Backtest End:']=track.index[-1].strftime("%Y-%m-%d")
    val=(track.index[-1]-track.index[0]).days+1
    total_days=val
    table_dic['Total Test Duration']=f'{val} days'
    
    val=utils.fmt_value(track_end['accu_fund'], pos_sign=False)
    table_dic['Cumulative Funding']=val
    
    val=utils.fmt_value(track_end['total_value'], pos_sign=False)
    val=f'{val} ({utils.fmt_value(track_end["total_value"]-track_end["accu_fund"], pos_sign=False)})'
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
   
    if drawdown>0:
        val=utils.fmt_value(cagr/drawdown,vtype='f')
        table_dic['MAR']=val
    else:
        table_dic['MAR']='NA'
   
    val=utils.fmt_value(
        track_end['norisk_total_value']/track_end['accu_fund']-1,vtype='pct')
    table_dic['No Risk ARR']=val 
    return table_dic