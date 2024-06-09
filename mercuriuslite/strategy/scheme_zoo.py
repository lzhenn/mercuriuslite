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
import os
from ..lib import const, utils, mathlib
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
    try:
        minerva.out_port=float(minerva.cfg['S_ma_cross']['out_portion'])
    except KeyError:
        minerva.out_port=1.0
    port_dic=minerva.pos_scheme(minerva, date)
    minerva.ticker_assets={}
    minerva.ma_cross={}
    trading_dates=minerva.trading_dates
    pseudo_flag=minerva.forward_flag
    # pseudo date for realtime trading
    #trading_dates_ext=trading_dates.append(
    #    pd.DatetimeIndex([trading_dates[-1]+datetime.timedelta(days=1)]))
    for idx, tgt in enumerate(minerva.port_tgts):
        idx_start=minerva.port_hist[tgt].index.searchsorted(date)
        ma_para_list=minerva.paras[idx].replace(' ','').split(',')
        ma_cross, shortlst, longlst=indicators.ma_crossover(
            minerva.port_hist[tgt], ma_para_list, 
            trunc_idx=idx_start, pseudo_flag=pseudo_flag)
        minerva.ticker_assets[tgt]=port_dic[tgt]*minerva.init_fund
        ma_cross=pd.DataFrame(ma_cross, index=trading_dates, columns=['signal'])
        minerva.ma_cross[tgt]=ma_cross
        minerva.ma_cross[f'{tgt}_short']=[ma_para_list[1],shortlst]
        minerva.ma_cross[f'{tgt}_long']=[ma_para_list[2],longlst]
def ma_cross(minerva, date):
    # current track rec
    curr_rec=minerva.track.loc[date]
    price_type=minerva.price_type
    out_port=minerva.out_port
    port_dic=minerva.pos_scheme(minerva, date)
    cash_min_ava=curr_rec['cash']-curr_rec['total_value']*port_dic['cash']
    ma_flag=False
    for tgt in minerva.port_tgts:
        port_portion=port_dic[tgt] # portion from config
        curr_hist=minerva.port_hist[tgt].loc[date]
        signal=minerva.ma_cross[tgt].loc[date].values[0]
        # current value
        minerva.ticker_assets[tgt]=curr_rec[f'{tgt}_share']*utils.determ_price(curr_hist, price_type)
        if signal != 0:
            ma_flag=True
        if signal == -1:
            minerva.action_dict[tgt]=minerva.ticker_assets[tgt]*out_port*(-1.0)
        if signal == 1: 
            minerva.action_dict[tgt]=min(curr_rec['total_value']*port_portion-minerva.ticker_assets[tgt],cash_min_ava)
    
    if minerva.new_fund:
        #  ma_cross+ or have existing position
        port_flag=[
            ((minerva.ticker_assets[tgt]/curr_rec['total_value'])/port_dic[tgt]>0.7) and (
                minerva.ma_cross[tgt].loc[date].values[0]>=0) for tgt in minerva.port_tgts]
        nexpose=sum(port_flag) 
        if nexpose > 0:
            for idx,tgt in enumerate(minerva.port_tgts):
                if port_flag[idx]:
                    minerva.action_dict[tgt]+=minerva.act_fund/nexpose
            minerva.trade(date, call_from='DCA',price_type=price_type)
        return
    if ma_flag:
        minerva.trade(date, call_from='MA_CROSS',price_type=price_type)
   
def ma_cross_rebalance(minerva, date):
    port_dic=minerva.pos_scheme(minerva, date)
    price_type=minerva.price_type
    curr_rec=minerva.track.loc[date]
    out_port=minerva.out_port
    action_dict = minerva.action_dict
    total_value=curr_rec['total_value']
    for tgt in minerva.port_tgts:
        curr_hist=minerva.port_hist[tgt].loc[date]
        minerva.ticker_assets[tgt]=curr_rec[f'{tgt}_share']*utils.determ_price(curr_hist, price_type)
        if (minerva.ticker_assets[tgt]/curr_rec['total_value'])/port_dic[tgt]>0.7:
            action_dict[tgt]=total_value*port_dic[tgt]-minerva.ticker_assets[tgt]
        else:
            action_dict[tgt]=0
    return action_dict
# ------------------------GRID_TRADING------------------------
def grid_trading_init(minerva, date):
    gridlist=minerva.cfg['S_grid_trading']['grid'].replace(' ','').split('/')
    minerva.price_type=minerva.cfg['S_grid_trading']['trade_price_type']
    minerva.grid=[]
    for itm in gridlist:
        unitlist=itm.replace(' ','').split(',')
        minerva.grid.append((float(unitlist[0]),int(unitlist[1]),int(unitlist[2])))
    pseudo_flag=minerva.forward_flag
    
    idx_start=minerva.basehist.index.searchsorted(date)
    grid_signal=indicators.grid_trading(
            minerva.basehist, minerva.grid, 
            trunc_idx=idx_start, pseudo_flag=pseudo_flag)
    minerva.grid_signal=pd.DataFrame(
        grid_signal, index=minerva.trading_dates, columns=['signal']) 
def grid_trading(minerva, date):
    # current track rec
    curr_rec=minerva.track.loc[date]
    drawdown=minerva.basehist['drawdown'][date]
    price_tpye=minerva.price_type
    grid_portion=minerva.grid
    
    
    dd_grid=[itm[0]/100.0 for itm in grid_portion]
    if minerva.new_fund:
        grid_lv=0
        for lv in dd_grid:
            if lv < drawdown:
                grid_lv+=1
            grid_lv=min(grid_lv, len(dd_grid)-1)
        for idx, tgt in enumerate(minerva.port_tgts):
            minerva.action_dict[tgt]=minerva.act_fund*grid_portion[grid_lv][idx+1]/100.0
        minerva.trade(date, call_from='DCA',price_type=price_tpye)
   
    else: 
        signal=minerva.grid_signal.loc[date].values[0]
        if signal != 0:
            for idx, tgt in enumerate(minerva.port_tgts):
                grid_lv=int(signal)
                minerva.action_dict[tgt]=minerva.act_fund*grid_portion[grid_lv-1][idx+1]/100.0
            minerva.trade(date, call_from='GRID_TRADING',price_type=price_tpye)

def grid_trading_rebalance(minerva, date):
    action_dict = minerva.action_dict
    port_dic=minerva.pos_scheme(minerva, date)
    curr_rec=minerva.track.loc[date]
    port_value=curr_rec['port_value']
    # only deleverage
    for tgt in minerva.port_tgts:
        action_dict[tgt]=port_value*port_dic[tgt]-curr_rec[f'{tgt}_value']
 
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

def fund_financing_init(minerva):
    try:
        finfile=minerva.cfg['S_fund_financing']['financing_file']
        if not(os.path.exists(finfile)):
            pass
        else:
            minerva.FIN_ACT=pd.read_csv(finfile, parse_dates=True, 
                index_col='Date')
    except KeyError:
        pass
    minerva.fin_nrdr=mathlib.ar2dr(const.NO_RISK_RETURN)
    minerva.fin_fund=minerva.init_fund 
def fund_financing(minerva, date):
    fin_act=minerva.FIN_ACT
    fund,dep_fund=0,0
    if date in minerva.cash_dates:
        fund=-(minerva.track.loc[date]['total_value']-minerva.fin_fund) # minus for outflow
    if date in fin_act.index:
        act=fin_act.loc[date]['action']
        if act=='rate':
            yoy=float(fin_act.loc[date]['value'])
            minerva.fin_nrdr=mathlib.ar2dr(yoy)
            utils.write_log(
                f'{print_prefix}[FINANCING] Refinancing signal captured, new rate: {utils.fmt_value(yoy,vtype="pct")} on {date.strftime("%Y-%m-%d")}.')
        elif act=='deposit':
            dep_fund=float(fin_act.loc[date]['value'])
            utils.write_log(
                f'{print_prefix}[FINANCING] Deposit signal captured, flow: {utils.fmt_value(dep_fund,pos_sign=False)} on {date.strftime("%Y-%m-%d")}.')
            minerva.fin_fund+=dep_fund
        elif act=='payment':
            frq=fin_act.loc[date]['value']
            minerva.cash_dates=utils.gen_date_intervals(
                minerva.dateseries, frq)
            utils.write_log(
                f'{print_prefix}[FINANCING] Payment Frequency signal captured, shift to {frq} on {date.strftime("%Y-%m-%d")}.')
    return fund+dep_fund # cash out
def fund_mutable(minerva, date):
    if date==minerva.dateseries[0]:
        return minerva.init_fund
    cfg=minerva.cfg
    mut_list=cfg['S_fund_mutable']['mutations'].replace(' ','').split(',')
    for mut in mut_list[::-1]:
        mutday,amount=mut.split(':')
        mutday=pd.to_datetime(mutday)
        if date>=mutday:
            return float(amount)
    return minerva.cash_flow

def fund_dynamic(minerva, date):
    # (drawdown, additional cashflow %)
    if date==minerva.dateseries[0]:
        return minerva.ini_fund
    portion_adj=[
        (0.6,8),(0.5,5),(0.4,3),(0.3,1.5),(0.2,1),(0.1,0.5)]
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
    NRDR=mathlib.ar2dr(norisk.loc[pretday]['Close']/100)
    return NRDR
