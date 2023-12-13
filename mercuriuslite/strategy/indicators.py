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

def ma_crossover(hist, para_lst, trunc_idx=0, pseudo_flag=False):
    '''
    calculate MA crossover
    pseudo_flag: True if use pseudo trading day data
    returns: -1: downward, 0, no signal, 1: upward
    '''
    pclose=False
    tgt_price,shortlag,longlag=para_lst[0],int(para_lst[1]),int(para_lst[2])
    
    if para_lst[0]=='PClose':
        tgt_price='Close'
        pclose=True
    ts=hist[tgt_price]
    ma_short=mathlib.ma(ts, shortlag)
    ma_long=mathlib.ma(ts, longlag)
    if pseudo_flag:
        ma_short[-1],ma_long[-1]=ma_short[-2],ma_long[-2]
    diff=ma_short-ma_long
    
    # signal is a vector of -1, 0, 1
    signal=np.sign(np.diff(np.sign(diff), prepend=0.0))
    
    # tranction from given start idx
    signal=signal[trunc_idx:]
    diff=diff[trunc_idx:]
   
    # set initial
    # Find the index of the first nonzero value in the signal array
    try:
        index = np.where(signal != 0)[0][0]
    except:
        if diff[0]>0:
            signal[0]=1
    # Set the value of signal[0] based on the value at the first nonzero index
    if 'index' in locals() and index>0:
        if signal[index] == -1:
            signal[0] = 1
        else:
            signal[0] = 0
    # if use previous trading day close, avoid future signal in trading
    if pclose:
        signal=np.concatenate(([0.0], signal[:-1]))
        diff=np.concatenate(([0.0], diff[:-1]))
    return signal, ma_short[-1], ma_long[-1]

def grid_trading(hist, para_lst, trunc_idx=0, pseudo_flag=False):
    '''
    calculate grid trading signal
    pseudo_flag: True if use pseudo trading day data
    returns: 0, no signal, 1-n: buying grid signal 
    '''
    drawdown=hist['drawdown'][trunc_idx:].values
    for lv, itm in enumerate(para_lst):
        gridlv=itm[0]/100.0
        drawdown=np.where((drawdown<gridlv) & (drawdown>0), lv, drawdown)
    signal=np.where((drawdown<1.0) & (drawdown>0), len(para_lst), drawdown)
    curr_lv=0.0
    for idx, ele in enumerate(signal.tolist()):
        if ele > curr_lv:
            curr_lv=ele
        else:
            if ele ==0:
                curr_lv=0
            signal[idx]=0.0
    return signal