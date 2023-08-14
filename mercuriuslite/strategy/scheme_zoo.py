#/usr/bin/env python3
"""strategy zoo"""

# ****************Available strategies*****************
#
#   buy_and_hold
#   gridding 
# ****************Available models*****************
print_prefix='strategy.zoo>>'
import numpy as np
from ..lib import const, utils
import datetime

# ------------------------Buy and Hold------------------------

def buy_and_hold(minerva, date):
    ''' buy and hold strategy'''
    port_rec=minerva.track.loc[date]
    cash = port_rec['cash']
    cash_portion=minerva.cash_scheme(minerva, date)
    #cash_portion=cash_fixed(minerva, date)
    ntgt=len(minerva.port_tgts)
    if (cash>cash_portion*port_rec['total_value']) and minerva.new_fund:
        port_dic=minerva.pos_scheme(minerva, date)
        cash_to_use=cash-cash_portion*port_rec['total_value']
        for tgt in minerva.port_tgts:
            minerva.action_dict[tgt]=cash_to_use*port_dic[tgt]
        minerva.new_fund=False
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
    portions=portions*(1-cash_portion)
    time_since_mjdown=0
    if hist.loc[date]['drawdown']<0.05:
        time_since_mjdown=utils.cal_days_since_mjdown(date,hist['drawdown'])/30
    # adjust by portfolio portion
    drawdown=hist.loc[date]['drawdown']*(1-cash_portion)
    for tgt,portion in zip(tgts,portions):
        if tgt in ['SPY','QQQ']:
            pos_dic[tgt]=portion-drawdown
        elif tgt in ['SPXL','TQQQ']:
            pos_dic[tgt]=max(portion+drawdown-time_since_mjdown*0.02,0)
        else:
            pos_dic[tgt]=portion
    return pos_dic


    pass 
def fund_fixed(minerva, date):
    infund=minerva.cash_flow
    return infund
def fund_dynamic(minerva, date):
    # (drawdown, additional cashflow %)
    portion_adj=[
        (0.3,10),(0.25,8),(0.2,6),(0.15,4),(0.1,2)]
    infund=minerva.cash_flow
    yesterday=date+datetime.timedelta(days=-1)
    drawdown=minerva.track.loc[yesterday]['drawdown']
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
        (0.3,-0.2),(0.25,-0.2),(0.2,-0.2),(0.15,-0.15),(0.1,-0.1),(0.05,-0.05)]
    balance_portion=const.CASH_IN_HAND
    drawdown_now=minerva.basehist.loc[date]['drawdown']
    for adj in portion_adj:
        drawdown_lv=adj[0]
        cash_portion_adj=adj[1]
        if drawdown_now>drawdown_lv:
            balance_portion+=cash_portion_adj
            break
    return balance_portion
    