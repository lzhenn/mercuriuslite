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
import os

# ---Module regime consts and variables---
print_prefix='lib.utils>>'


# ---Classes and Functions---

def trim_hist(hist):
    ''' trim hist '''
    start_dates, end_dates =[],[] 
    for ticker in hist.keys():
        start_dates.append(hist[ticker].index[0])
        end_dates.append(hist[ticker].index[-1])
    start_date=sorted(start_dates)[-1]
    end_date=sorted(end_dates)[0]
    for ticker in hist.keys():
        hist[ticker]=hist[ticker].loc[start_date:end_date]
    write_log(f'{print_prefix}Mercurius.trim_hist()...valid from {start_date} to {end_date}')
    return hist, len(hist[ticker])
def form_scheme_fig_fn(cfg,suffix=''):
    fig_path=cfg['POSTPROCESS']['fig_path']
    fn_lst=[cfg['SCHEMER']['scheme_name']]
    tgts=cfg['SCHEMER']['port_tgts'].replace(' ','').replace(',','_')
    fn_lst.append(tgts)
    if cfg['SCHEMER'].getboolean('forward_flag'):
        fn_lst.append('forward')
    elif cfg['SCHEMER'].getboolean('backtest_flag'):
        fn_lst.append('backtest')
    if suffix!='':
        fn_lst.append(suffix)
    fn_lst.append('png')
    
    try:
        fn=cfg['POSTPROCESS']['fig_fn']
        if suffix!='':
            fn=fn+'.'+suffix
        fn=os.path.join(fig_path,f'{fn}.png') 
    except KeyError:
        fn=os.path.join(fig_path,'.'.join(fn_lst)) 
    return fn
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
    track['daily_net_return']=1.0
    track['lev_value']=0.0
    track['net_value']=0.0
    track['lev_ratio']=1.0
    for ticker in tgts:
        track[f'{ticker}_value']=0.0
        track[f'{ticker}_share']=0

    return track
# ------------ cal_funcs for historical data ------------
def cal_tr(hist):
    '''
    calculate true range
    '''
    tr=np.zeros(len(hist))
    o,l,h,c=hist['Open'],hist['Low'].values,hist['High'].values,hist['Close'].values
    tr_mtx=np.array((h[1:]-l[1:],abs(h[1:]-c[0:-1]),abs(c[0:-1]-l[0:-1])))
    tr=tr_mtx.max(axis=0)
    tr=np.insert(tr, 0, h[0]-l[0], axis=0)
    tr=tr/o
    return tr
def cal_daychange(hist): 
    '''
    calculate day change
    '''
    dc=np.zeros(len(hist))
    c=hist['Close'].values
    dc=np.diff(c, prepend=c[0])/c
    return dc

def cal_drawdown(hist):
    '''
    calculate drawdown
    '''
    dd=(hist['Close'].cummax() - hist['Close']) / hist['Close'].cummax()
    return dd

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
def parse_endtime(dt_str): 
    if not(dt_str=='0'):
        return datetime.datetime.strptime(dt_str, '%Y%m%d')
    else: 
        dt=datetime.datetime.now()
        '''
        dt_us=dt+datetime.timedelta(days=-1) # eastern time
        ymd=dt_us.strftime('%Y%m%d')
        if ymd in const.HOLIDAYS:
            dt+=datetime.timedelta(days=-1)
        if dt.weekday() == 6:
            dt+=datetime.timedelta(days=-1)
        elif dt.weekday() == 0:
            dt+=datetime.timedelta(days=-2)
        '''
    return dt

def parse_file_names(fns):
    if fns.strip().lower() in ['','none']:
        return []
    fn_lst=fns.replace(' ','').split(',')
    return fn_lst
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

def cal_flow(act_df, ticker):
    # filter dataframe by ticker name
    buy_df = act_df[(act_df['ticker'] == ticker) & (act_df['share'] > 0)]
    sell_df = act_df[(act_df['ticker'] == ticker) & (act_df['share'] < 0)]
    total_inflow = (buy_df['share'] * buy_df['price']).sum()
    total_outflow = (sell_df['share'] * sell_df['price']).sum()
    return total_inflow, total_outflow
def cal_days_since_mjdown(date, drawdown, thresh=0.05):
    dates=drawdown.index
    date_pos=date
    while (date_pos in dates) and (drawdown[date_pos]<thresh):
        date_pos=dates[dates.get_loc(date_pos)-1]
    return (date-date_pos).days

def find_trade_date(date, dates):
    if date in dates:
        trade_day=date
    else:
        idx = np.searchsorted(dates, date, side='left')
        if idx==len(dates):
            idx=-1
        trade_day=dates[idx]
    return trade_day

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

def fmt_value(val, vtype='usd', pos_sign=True):
    # vtype='usd','pct'
    if issubclass(type(val), str):
        return val
    if vtype=='usd':
        fmt_val=f'${val:.2f}'
        if pos_sign and val>0:
            fmt_val=f'+${val:.2f}'
    elif vtype=='cny':
        fmt_val=f'{val:.2f}元'
        if pos_sign and val>0:
            fmt_val=f'+{val:.2f}元'
    elif vtype=='pct':
        if val>=0:
            if pos_sign:
                fmt_val=f'+{val:.2%}'
            else:
                fmt_val=f'{val:.2%}'
        else:
            fmt_val=f'{val:.2%}'
    elif vtype=='f':
        fmt_val=f'{val:.2f}'
    else:
        fmt_val=val
    return fmt_val

def frq_to_frqCN(frq): 
    if frq=='none':
        fin_pay_frq='总额累积（最终还款日一次性付息）'
    elif frq=='QS':
        fin_pay_frq='季度支付（每季度付息一次）'
    elif frq=='MS':
        fin_pay_frq='月度支付（每月付息一次）'
    elif frq=='M':
        fin_pay_frq='月度支付（每月末付息一次）'
    elif frq=='2QS':
        fin_pay_frq='半年支付（每半年付息一次）'
    elif frq=='YS':
        fin_pay_frq='年度支付（每年付息一次）' 
    elif frq=='W':
        fin_pay_frq='周支付（每周付息一次）'
    elif frq=='D':
        fin_pay_frq='日支付（每日付息一次）'
    return fin_pay_frq 
# ---Unit test---
if __name__ == '__main__':
    pass
