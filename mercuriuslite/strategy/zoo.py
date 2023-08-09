#/usr/bin/env python3
"""strategy zoo"""

# ****************Available strategies*****************
#
#   buy_and_hold
#   gridding 
# ****************Available models*****************
print_prefix='strategy.zoo>>'


# ------------------------Buy and Hold------------------------

def buy_and_hold(minerva, date):
    ''' buy and hold strategy'''
    port_rec=minerva.track.loc[date]
    cash = port_rec['cash']
    if cash>0:
        ntgt=len(minerva.port_tgts)
        for tgt in minerva.port_tgts:
            minerva.action_dict[tgt]=cash*1.0/ntgt
        minerva.pos_manage()
    exit()