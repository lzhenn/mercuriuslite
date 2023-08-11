#/usr/bin/env python3
"""strategy zoo"""

# ****************Available strategies*****************
#
#   buy_and_hold
#   gridding 
# ****************Available models*****************
print_prefix='strategy.zoo>>'
from ..lib import const, utils

# ------------------------Buy and Hold------------------------

def buy_and_hold(minerva, date):
    ''' buy and hold strategy'''
    port_rec=minerva.track.loc[date]
    cash = port_rec['cash']
    ntgt=len(minerva.port_tgts)
    if (cash>const.CASH_IN_HAND*port_rec['total_value']) and minerva.new_fund:
        cash_to_use=cash-const.CASH_IN_HAND*port_rec['total_value']
        for tgt in minerva.port_tgts:
            minerva.action_dict[tgt]['value']=cash_to_use*minerva.pos_dic[tgt]
        minerva.new_fund=False
        minerva.pos_manage(date)