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

def ma_crossover(hist, tgt='Close', shortlag=9, longlag=21):
    '''
    calculate MA crossover
    returns: -1: downward, 0, no signal, 1: upward
    '''
    ts=hist[tgt]
    ma_short=mathlib.ma(ts, shortlag)
    ma_long=mathlib.ma(ts, longlag)
    diff=ma_short-ma_long
    signal=np.sign(np.diff(np.sign(diff)))
    return signal