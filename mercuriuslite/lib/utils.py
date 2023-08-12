#/usr/bin/env python3
"""
    Commonly used utilities

    Function    
    ---------------
    throw_error(msg):
        throw error and exit
    
    write_log(msg, lvl=20):
        write logging log to log file
    
    parse_tswildcard(tgt_time, wildcard):
        parse string with timestamp wildcard 
        to datetime object

"""
# ---imports---
import logging, datetime
import pandas as pd
import numpy as np
from . import const

# ---Module regime consts and variables---
print_prefix='lib.utils>>'


# ---Classes and Functions---
def throw_error(msg):
    '''
    throw error and exit
    '''
    logging.error(msg)
    exit()

def write_log(msg, lvl=20):
    '''
    write logging log to log file
    level code:
        CRITICAL    50
        ERROR   40
        WARNING 30
        INFO    20
        DEBUG   10
        NOTSET  0
    '''

    logging.log(lvl, msg)


def parse_lead(ytgt):
    '''
    parse string with timestamp wildcard to datetime object
    '''
    if len(ytgt.split('_'))==1:
        lead_str='1day'
    else:
        lead_str=ytgt.split('_')[-1]
    
    ytgt=ytgt.split('_')[0]
    trad_day=cal_trade_day(lead_str) 
    return ytgt, trad_day

def cal_trade_day(lead_str):
    for key_wd in ['day','week','mon','qtr','yr']:
        if key_wd in lead_str:
            return int(lead_str.replace(key_wd,''))*const.TRAD_DAYS[key_wd]
    if lead_str == 'none':
        return -1
    throw_error(f'key lead str (day, week, mon, yr) not found: {lead_str}')

def gen_date_intervals(dateseries, interval):
    for key_wd in ['W','M','Q','Y']:
        if key_wd in interval:
            dates=pd.date_range(start=dateseries[1], end=dateseries[-1], freq=key_wd)
            return dates.to_list()
    if interval == 'none':
        return []
   
def parse_intime(dt_str):
    if not(dt_str=='0'):
        return datetime.datetime.strptime(dt_str, '%Y%m%d')
    else: 
        return dt_str 
def parse_tswildcard(tgt_time, wildcard):
    '''
    parse string with timestamp wildcard to datetime object
    '''
    seg_str=wildcard.split('@')
    parsed_str=''
    for seg in seg_str:
        if seg.startswith('%'):
            parsed_str+=tgt_time.strftime(seg)
        else:
            parsed_str+=seg
    return parsed_str

def cal_trade(price, cash_in):
    share=np.floor(cash_in/price)
    cash_left=cash_in-share*price
    return share, cash_left

def cal_exposure_assign(tgts, portions):
    pass
# ---Unit test---
if __name__ == '__main__':
    pass

def fmt_value(val, vtype='usd', dec=2):
    # vtype='usd','pct'
    
    if vtype=='usd':
        fmt_val=f'${val:.2f}'
    if vtype=='pct':
        if val>=0:
            fmt_val=f'+{val:.2%}'
        else:
            fmt_val=f'{val:.2%}'
    return fmt_val 