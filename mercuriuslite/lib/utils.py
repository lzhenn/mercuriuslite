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

def init_track(dates, tgts):
    track=pd.DataFrame(
        np.zeros(len(dates)), index=dates, columns=['accu_fund'])
    track.index.name='Date'
    track['cash']=0.0
    track['port_value']=0.0
    track['total_value']=0.0
    track['norisk_total_value']=0.0
    track['daily_return']=1.0
    for ticker in tgts:
        track[f'{ticker}_value']=0.0
        track[f'{ticker}_share']=0

    return track
def cal_trade_day(lead_str):
    for key_wd in ['day','week','mon','qtr','yr']:
        if key_wd in lead_str:
            return int(lead_str.replace(key_wd,''))*const.TRAD_DAYS[key_wd]
    if lead_str == 'none':
        return -1
    throw_error(f'{print_prefix}key lead str (day, week, mon, yr) not found: {lead_str}')
def real_acc_dates(acc_rec, tgt='cash'):
    acc_dates=acc_rec[acc_rec['ticker']==tgt]['Date']
    return acc_dates.values

def construct_msg(scheme_name, date):
    msg_dic={
        'title_lst':[f'MercuriusLite Strategy: {scheme_name}','Summary',f'{date.strftime("%Y/%m/%d")}'],
        'msg_body':''
    }
    return msg_dic
def feed_msg_title(msg_dic, op_keyword):
    if msg_dic['title_lst'][1]=='Summary':
        msg_dic['title_lst'][1]=f'|{op_keyword}|'
    else:
        msg_dic['title_lst'][1]+=f'{op_keyword}|'
    return msg_dic
def feed_msg_body(msg_dic, content): 
    msg_dic['msg_body']+=f'{content}\n'    
    return msg_dic

def form_msg(msg_dic):
    title='|'.join(msg_dic['title_lst'])
    msg=msg_dic['msg_body']
    return title, msg

def init_operation_df():
    return pd.DataFrame(columns=['Date', 'ticker', 'share', 'price'])
def gen_date_intervals(dateseries, interval):
    if interval=='none':
        return []
    elif interval=='real':
        return 'real'
    try:
        dates=pd.date_range(start=dateseries[1], end=dateseries[-1], freq=interval)
        return dates.to_list()
    except:
        throw_error(f'{print_prefix}invalid date interval: {interval}')
   
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


def cal_days_since_mjdown(date, drawdown, thresh=0.05):
    dates=drawdown.index
    date_pos=date
    while (date_pos in dates) and (drawdown[date_pos]<thresh):
        date_pos=dates[dates.get_loc(date_pos)-1]
    return (date-date_pos).days


def determ_price(price_rec, price_type):
    if price_type in ['High', 'Low', 'Close', 'Open']:
        price=price_rec[price_type]
    elif price_type=='Mid':
        price=(price_rec['High']+price_rec['Low'])/2
    elif price_type=='MidOC':
        price=(price_rec['Open']+price_rec['Close'])/2
    elif price_type=='Avg':
        price=(price_rec['Open']+price_rec['Close']+price_rec['High']+price_rec['Low'])/4
    elif price_type=='NearOpen':
        price=price_rec['Open']*0.8+price_rec['High']*0.1+price_rec['Low']*0.1
    elif price_type=='Random':
        price=np.random.uniform(low=price_rec['Low'],high=price_rec['High'])
    return price

def fmt_value(val, vtype='usd', dec=2):
    # vtype='usd','pct'
    if vtype=='usd':
        fmt_val=f'${val:.2f}'
    if vtype=='pct':
        if val>=0:
            fmt_val=f'+{val:.2%}'
        else:
            fmt_val=f'{val:.2%}'
    if vtype=='f':
        fmt_val=f'{val:.2f}'
        
    return fmt_val 
# ---Unit test---
if __name__ == '__main__':
    pass
