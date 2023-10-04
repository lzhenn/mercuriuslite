#!/usr/bin/env python3
"""strategy zoo"""

# ****************Available strategies*****************
#   --Portfolio
#       buy_and_hold
#
#   --position
#       pos_prescribe
#       pos_seesaw
#
#   --funding
#       fund_fixed
#       fund_dynamic
#
#   --cash
#       cash_fixed
#       cash_dynamic
#
#   --norisk
#       norisk_fixed
#       norisk_dynamic
#
# ****************Available models*****************
print_prefix='strategy.zoo>>'
import numpy as np
import pandas as pd
from ..lib import const, utils, mathlib, io
from . import indicators
import datetime

# ------------------------Buy and Hold------------------------

def buy_and_hold_init(minerva, date):
    pass
def buy_and_hold(minerva, date):
    ''' buy and hold strategy'''
    port_rec=minerva.track.loc[date]
    cash = port_rec['cash']
    #cash_portion=cash_fixed(minerva, date)
    ntgt=len(minerva.port_tgts)
    port_dic=minerva.pos_scheme(minerva, date)
    cash_to_use=cash-port_dic['cash']*port_rec['total_value']
    if cash_to_use>0:
        for tgt in minerva.port_tgts:
            minerva.action_dict[tgt]=cash_to_use*port_dic[tgt]
        minerva.trade(date)

def buy_and_hold_rebalance(minerva, date):
    return minerva.action_dict
# ------------------------MA_CROSS------------------------
def ma_cross_init(minerva, date):
    minerva.paras=minerva.cfg['S_ma_cross']['paras'].replace(' ','').split('/')
    minerva.price_type=minerva.cfg['S_ma_cross']['trade_price_type']
    port_dic=minerva.pos_scheme(minerva, date)
    minerva.ticker_assets={}
    minerva.ma_cross={}
    trading_dates=minerva.trading_dates
    # pseudo date for realtime trading
    #trading_dates_ext=trading_dates.append(
    #    pd.DatetimeIndex([trading_dates[-1]+datetime.timedelta(days=1)]))
    for idx, tgt in enumerate(minerva.port_tgts):
        idx_start=minerva.port_hist[tgt].index.searchsorted(date)
        ma_para_list=minerva.paras[idx].replace(' ','').split(',')
        ma_cross, shortlst, longlst=indicators.ma_crossover(
            minerva.port_hist[tgt], ma_para_list, 
            trunc_idx=idx_start)
        minerva.ticker_assets[tgt]=port_dic[tgt]*minerva.init_fund
        ma_cross=pd.DataFrame(ma_cross, index=trading_dates, columns=['signal'])
        minerva.ma_cross[tgt]=ma_cross
        minerva.ma_cross[f'{tgt}_short']=[ma_para_list[1],shortlst]
        minerva.ma_cross[f'{tgt}_long']=[ma_para_list[2],longlst]
def ma_cross(minerva, date):
    # current track rec
    curr_rec=minerva.track.loc[date]
    price_tpye=minerva.price_type
    ma_flag=False
    for tgt in minerva.port_tgts:
        curr_hist=minerva.port_hist[tgt].loc[date]
        signal=minerva.ma_cross[tgt].loc[date].values[0]
        if signal != 0:
            ma_flag=True
        if signal == -1:
            minerva.ticker_assets[tgt]=curr_rec[f'{tgt}_share']*utils.determ_price(curr_hist, price_tpye)
        minerva.action_dict[tgt]=minerva.ticker_assets[tgt]*signal
    if minerva.new_fund:
        port_flag=[
            (curr_rec[f'{tgt}_share']>0) and (
                minerva.ma_cross[tgt].loc[date].values[0]>=0) for tgt in minerva.port_tgts]
        nexpose=sum(port_flag) 
        if nexpose > 0:
            for idx,tgt in enumerate(minerva.port_tgts):
                if port_flag[idx]:
                    minerva.action_dict[tgt]+=minerva.act_fund/nexpose
        minerva.trade(date, call_from='DCA',price_type=price_tpye)
        return
    if ma_flag:
        minerva.trade(date, call_from='MA_CROSS',price_type=price_tpye)
   
def ma_cross_rebalance(minerva, date):
    port_dic=minerva.pos_scheme(minerva, date)
    curr_rec=minerva.track.loc[date]
    action_dict = minerva.action_dict
    total_value=curr_rec['total_value']
    for tgt in minerva.port_tgts:
        curr_hist=minerva.port_hist[tgt].loc[date]
        minerva.ticker_assets[tgt]=total_value*port_dic[tgt]
        if curr_rec[f'{tgt}_share']>0:
            action_dict[tgt]=total_value*port_dic[tgt]-curr_rec[f'{tgt}_share']*utils.determ_price(curr_hist, 'Open')
        else:
            action_dict[tgt]=0
    return action_dict
# =================== For postion schemes
def pos_prescribe(minerva, date):
    pos_dic={}
    tgts=minerva.port_tgts
    portions=minerva.cfg['S_prescribe']['pos_portion'].replace(' ','').split(',')
    
    cash_portion=minerva.cash_scheme(minerva, date)
    pos_dic['cash']=cash_portion 
    portions=[float(port) for port in portions][0:len(tgts)]
    portions=np.asarray(portions)
    portions=portions/portions.sum()
    
    sum_tgt=portions.sum()
    # normalize
    for tgt,portion in zip(tgts,portions):
        pos_dic[tgt]=(portion/sum_tgt)*(1-cash_portion)
    return pos_dic

def pos_seesaw(minerva, date):
    pos_dic={}
    tgts=minerva.port_tgts
    hist=minerva.basehist
    portions=minerva.cfg['S_seesaw']['pos_portion'].replace(' ','').split(',')
    portions=[float(port) for port in portions][0:len(tgts)]
    portions=np.asarray(portions)
    portions=portions/portions.sum()
    
    cash_portion=minerva.cash_scheme(minerva, date)
    pos_dic['cash']=cash_portion 
    # adjust by portfolio portion
    drawdown=hist.loc[date]['drawdown']
   
    defense=0.0
    if drawdown<0.05:
        defense=indicators.new_high_defense(hist, date)
    
    sum_tgt=0.0
    for tgt,portion in zip(tgts,portions):
        if tgt in ['SPY','QQQ']:
            pos_dic[tgt]=portion-drawdown+defense
        elif tgt =='SPXL':
            pos_dic[tgt]=min(max(portion+drawdown-defense,0.00),0.35)
        elif tgt =='TQQQ':
            pos_dic[tgt]=portion
        else:
            pos_dic[tgt]=portion
        sum_tgt+=pos_dic[tgt]
    # normalize ticker's portion
    for tgt,portion in zip(tgts,portions):
        pos_dic[tgt]=(pos_dic[tgt]/sum_tgt)*(1-cash_portion)
    #print(f'drawdown: {drawdown}')
    return pos_dic
# ================== For funding schemes
def fund_fixed(minerva, date):
    if date==minerva.dateseries[0]:
        return minerva.init_fund
    infund=minerva.cash_flow
    return infund

def fund_real(minerva, date):
    ra=minerva.real_acc
    infund=ra.loc[ra['Date']==date]
    infund=infund.loc[infund['ticker']=='cash']
    infund=infund['price'].values[0]
    return infund

def fund_dynamic(minerva, date):
    # (drawdown, additional cashflow %)
    if date==minerva.dateseries[0]:
        return minerva.ini_fund
    
    portion_adj=[
        (0.3,8),(0.25,6),(0.2,4),(0.15,2),(0.1,1),(0.05,0.5)]
    infund=minerva.cash_flow
    hist=minerva.basehist
    pretday=date+datetime.timedelta(days=-1)
    while (pretday not in hist.index) and (pretday>hist.index[0]):
        pretday=pretday-datetime.timedelta(days=1)
    drawdown=hist.loc[pretday]['drawdown']
    for adj in portion_adj:
        drawdown_lv=adj[0]
        cash_portion_adj=adj[1]
        if drawdown>drawdown_lv:
            infund=minerva.cash_flow*(1+adj[1])
            break
    return infund

# ================== For cash schemes
def cash_fixed(minerva, date):
    return const.CASH_IN_HAND

def cash_dynamic(minerva, date):
    # (drawdown, cash_change)
    
    portion_adj=[
        (0.3,-0.2),(0.25,-0.2),(0.2,-0.2),
        (0.15,-0.15),(0.1,-0.1),(0.05,-0.05)]
    
    balance_portion=const.CASH_IN_HAND
    
    # alter by norisk interest
    NRYR=mathlib.dr2ar(minerva.NRDR)
    balance_portion=balance_portion+(NRYR-1)*2.0
     
    if date==minerva.track.index[0]:
        return balance_portion
    
    rec_now=minerva.track.loc[date]
    cash_portion_now=rec_now['cash']/rec_now['total_value']
    drawdown_now=minerva.basehist.loc[date]['drawdown']
    
    # drawdown<5%
    if drawdown_now<0.05:
        add_cash=indicators.new_high_defense(minerva.basehist, date)
        return add_cash+balance_portion
    
    # drawdown>=5%
    for adj in portion_adj:
        drawdown_lv=adj[0]
        cash_portion_adj=adj[1]
        if drawdown_now>=drawdown_lv:
            balance_portion+=cash_portion_adj
            cash_portion_now+=cash_portion_adj
            break
    return min(const.CASH_IN_HAND*1.5,
        max(cash_portion_now,balance_portion,const.CASH_IN_HAND*0.5))
# ================== For norisk schemes
def norisk_fixed(minerva, date):
    NRDR=mathlib.ar2dr(const.NO_RISK_RETURN)
    return NRDR
def norisk_dynamic(minerva, date):
    norisk=minerva.noriskhist
    pretday=date+datetime.timedelta(days=-1)
    while (pretday not in norisk.index) and (pretday>norisk.index[0]):
        pretday=pretday-datetime.timedelta(days=1)
    NRDR=mathlib.ar2dr(norisk.loc[pretday]['Close']/100*0.8)
    return NRDR
