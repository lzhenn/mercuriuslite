from ..lib import const, utils, mathlib
import numpy as np
def new_high_defense(hist, date):
    
    time_since_mjdown=utils.cal_days_since_mjdown(
        date, hist['drawdown'], thresh=const.MAJOR_DRAWDOWN)/const.DAYS_PER_MONTH
    
    # one month no major drawdown, add % defensive portion
    defense=0.01*time_since_mjdown
    if defense>0.5*const.CASH_IN_HAND:
        defense=0.5*const.CASH_IN_HAND
    return defense

def ma_crossover(hist, para_lst):
    '''
    calculate MA crossover
    returns: -1: downward, 0, no signal, 1: upward
    '''
    tgt_price,shortlag,longlag=para_lst[0],int(para_lst[1]),int(para_lst[2])
    ts=hist[tgt_price]
    ma_short=mathlib.ma(ts, shortlag)
    ma_long=mathlib.ma(ts, longlag)
    diff=ma_short-ma_long
    signal=np.sign(np.diff(np.sign(diff), prepend=0.0))
    # signal is a vector of -1, 0, 1
    return signal