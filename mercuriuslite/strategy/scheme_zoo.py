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
    ntgt=len(minerva.port_tgts)
    port_dic=minerva.pos_scheme(minerva, date)
    if (cash>const.CASH_IN_HAND*port_rec['total_value']) and minerva.new_fund:
        cash_to_use=cash-const.CASH_IN_HAND*port_rec['total_value']
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
    portions=minerva.cfg['S_seesaw']['pos_portion'].replace(' ','').split(',')
    
    portions=[float(port) for port in portions]
    portions=np.asarray(portions)
    portions=portions/portions.sum()
    
    drawdown=minerva.basehist.loc[date]['drawdown']
    for tgt,portion in zip(tgts,portions):
        if tgt=='SPY':
            pos_dic[tgt]=portion-drawdown
        elif tgt=='SPXL':
            pos_dic[tgt]=portion+drawdown
        else:
            pos_dic[tgt]=portion
    return pos_dic


    pass 
def fund_fixed(minerva, date):
    infund=minerva.cash_flow
    return infund
def fund_dynamic(minerva, date):
    infund=minerva.cash_flow
    yesterday=date+datetime.timedelta(days=-1)
    drawdown=minerva.track.loc[yesterday]['drawdown']
    if drawdown>0.05:
        infund=minerva.cash_flow*(drawdown/0.05)
    return infund
    