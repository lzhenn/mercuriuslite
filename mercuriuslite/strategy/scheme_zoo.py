#/usr/bin/env python3
"""strategy zoo"""

# ****************Available strategies*****************
#
#   buy_and_hold
#   gridding 
# ****************Available models*****************
print_prefix='strategy.zoo>>'
import numpy as np
from ..lib import const, utils, mathlib, io
import datetime

# ------------------------Buy and Hold------------------------

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
# =================== For postion schemes
def pos_prescribe(minerva, date):
    pos_dic={}
    tgts=minerva.port_tgts
    portions=minerva.cfg['S_prescribe']['pos_portion'].replace(' ','').split(',')
    
    portions=[float(port) for port in portions]
    portions=np.asarray(portions)
    portions=portions/portions.sum()
    for tgt,portion in zip(tgts,portions):
        pos_dic[tgt]=portion
    return pos_dic

def pos_seesaw(minerva, date):
    pos_dic={}
    tgts=minerva.port_tgts
    hist=minerva.basehist
    portions=minerva.cfg['S_seesaw']['pos_portion'].replace(' ','').split(',')
    portions=[float(port) for port in portions]
    portions=np.asarray(portions)
    portions=portions/portions.sum()
    
    cash_portion=minerva.cash_scheme(minerva, date)
    pos_dic['cash']=cash_portion 
    # adjust by portfolio portion
    drawdown=hist.loc[date]['drawdown']
   
    defense=0.0
    if drawdown<0.05:
        defense=new_high_defense(hist, date)
    
    sum_tgt=0.0
    for tgt,portion in zip(tgts,portions):
        if tgt in ['SPY','QQQ']:
            pos_dic[tgt]=portion-drawdown+defense
        elif tgt =='SPXL':
            pos_dic[tgt]=min(max(portion+drawdown-defense,0.00),0.35)
        elif tgt =='TQQQ':
            pos_dic[tgt]=min(max(portion+0.5*drawdown-defense,0.00),0.25)
            
        else:
            pos_dic[tgt]=portion
        sum_tgt+=pos_dic[tgt]
    # normalize
    for tgt,portion in zip(tgts,portions):
        pos_dic[tgt]=(pos_dic[tgt]/sum_tgt)*(1-cash_portion)
    #print(f'drawdown: {drawdown}')
    return pos_dic

def fund_fixed(minerva, date):
    infund=minerva.cash_flow
    return infund

def fund_dynamic(minerva, date):
    # (drawdown, additional cashflow %)
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
        add_cash=new_high_defense(minerva.basehist, date)
        return add_cash+balance_portion
    
    # drawdown>=5%
    for adj in portion_adj:
        drawdown_lv=adj[0]
        cash_portion_adj=adj[1]
        if drawdown_now>=drawdown_lv:
            balance_portion+=cash_portion_adj
            cash_portion_now+=cash_portion_adj
            break
    return min(const.CASH_IN_HAND*1.5,max(cash_portion_now,balance_portion,0.05))

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

def new_high_defense(hist, date):
    
    time_since_mjdown=utils.cal_days_since_mjdown(
        date, hist['drawdown'], thresh=const.MAJOR_DRAWDOWN)/const.DAYS_PER_MONTH
    
    # one month no major drawdown, add 2% defensive portion
    defense=0.01*time_since_mjdown
    if defense>0.5*const.CASH_IN_HAND:
        defense=0.5*const.CASH_IN_HAND
    return defense