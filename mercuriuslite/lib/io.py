#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
from sklearn.model_selection import train_test_split
import numpy as np
import json
import pandas as pd
import datetime, os
from . import utils, cfgparser, mathlib

# ---Module regime consts and variables---
print_prefix='lib.io>>'

date_parser = lambda date: datetime.datetime.strptime(
    date.split()[0],'%Y-%m-%d')

# ---Classes and Functions---

def archive_msg(fn, title, msg):
    
    dic={'title':title, 'msg_body':msg, 'date':datetime.datetime.now().strftime('%Y-%m-%d')}
    with open(fn, 'w') as f:
        json.dump(dic, f)
def load_msg(fn):
    with open(fn, 'r') as f:
        dic=json.load(f)
    return dic
def load_xy(
        Xfile, Xnames, Yfile, Ytgt, Ylead, start_time='0', end_time='0'):
    
    Y, date_series =load_y(Yfile, Ytgt, start_time, end_time)
    
    X =load_x(Y, Xfile, Xnames, start_time, end_time)
    
    if Ylead >0: 
        X, Y, date_series = match_xy(X, Y, Ylead, date_series)
    
    check_xy(X,Y)

    return X, Y, date_series 
    #self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(
    #        self.X, self.Y, test_size=self.test_size, shuffle=False)
def load_hist(dbpath, tgt, add_pseudo=False, dateseries=None):
    ''' load historical data accroding to dbpath and tgt '''
    fn_path=os.path.join(dbpath, tgt+'.csv')
    tgt_hist=pd.read_csv(fn_path, parse_dates=True, 
        date_parser=date_parser, index_col='Date')
    if add_pseudo:
        # add last day pseudo record
        new_row=tgt_hist.iloc[-1]
        tgt_hist = tgt_hist.append(new_row, ignore_index=False)
        tgt_hist = tgt_hist.reset_index()
        date_last=tgt_hist.iloc[-1]['Date']
        tgt_hist['Date'].values[-1] = date_last+datetime.timedelta(days=1)
        tgt_hist = tgt_hist.set_index('Date')
        tgt_hist.iloc[-1]['High']=tgt_hist.iloc[-1]['High']-tgt_hist.iloc[-1]['Open']+tgt_hist.iloc[-1]['Close']
        tgt_hist.iloc[-1]['Low']=tgt_hist.iloc[-1]['Low']-tgt_hist.iloc[-1]['Open']+tgt_hist.iloc[-1]['Close']
        tgt_hist.iloc[-1]['Open']=tgt_hist.iloc[-1]['Close']
        tgt_hist.iloc[-1]['Close']=(tgt_hist.iloc[-1]['High']+tgt_hist.iloc[-1]['Low'])/2
    if dateseries is not None:
        tgt_hist=tgt_hist.loc[dateseries]
    return tgt_hist
def load_real_acc(acc_file):
    ''' load real account trading history '''

    acc_real=pd.read_csv(acc_file, parse_dates=True)
    acc_real['Date'] = pd.to_datetime(
        acc_real['Date'], format='%Y%m%d')
    return acc_real
def match_xy(X,Y,lead_days, date_series):
    Y=Y[lead_days:]/Y[:-lead_days]-1
    X=X[:-lead_days]
    date_series=date_series[lead_days:]
    return X, Y, date_series
def load_y(Yfile, Ytgt, start_time='0', end_time='0', call_from='train'):
    ''' select y according to prescribed method '''
    lb_all=pd.read_csv(Yfile, 
        parse_dates=True, date_parser=date_parser, index_col='Date')
    if start_time == '0':
        start_time=lb_all.index[0]
    if end_time == '0':
        end_time=lb_all.index[-1]
    Y=lb_all[Ytgt][start_time:end_time].values
    date_series=lb_all[start_time:end_time].index
    return Y, date_series 

def load_x(Y, Xfile, Xnames, start_time='0', end_time='0', call_from='train'):
    ''' load feature lib '''
    if Xfile == 'na':
        X=gen_auto_x(Y, Xnames)
    return X
def gen_auto_x(Y, Xnames):
    Xnames=Xnames.replace(' ','').split(',')
    X = np.zeros((len(Y), len(Xnames)))
    for i, name in enumerate(Xnames):
        k = int(name.split('_')[1])
        if name.startswith('mtm_'):
            X[k:, i] = (Y[k:] - Y[:-k])/Y[k:]
        elif name.startswith('ma_'):
            X[:, i] = mathlib.ma(Y, k) 
        elif name.startswith('dma_'):
            X[:, i] = 1-mathlib.ma(Y, k)/Y
        elif name.startswith('bollpct_'): 
            X[:, i] = mathlib.bollpct(Y, k)
        else:
            raise ValueError('Invalid feature name: {}'.format(name))
    return X

def select_x(self, flib, call_from):
    ''' select x according to prescribed method '''
    if call_from == 'train':
        strt_time=self.model_start_time
        end_time=self.model_end_time
    elif call_from== 'cast':
        strt_time=self.infer_start_time
        end_time=self.infer_end_time
    X=flib.loc[strt_time:end_time]
    self.Xdate=X.index
    self.X=X.values
    self.Xnames=flib.columns.values.tolist()

def check_xy(X,Y):
    if X.shape[0] != Y.shape[0]:
        utils.throw_error(print_prefix+'Size of dim0 in X and Y does not match!')
    else:
        utils.write_log(
            f'{print_prefix}Y Size:{Y.shape},first five:{Y[:5]}, and last five:{Y[-5:]}')
        utils.write_log(
            f'{print_prefix}X Size:{X.shape},first five:{X[:5].T}, and last five:{X[-5:].T}')

def load_model(model_dir, model_name, ticker, baseline=False):
    if model_name in ['plainhist', 'svpdf']:
        return load_model_npy(model_dir, model_name, ticker, baseline)
    
def load_model_npy(model_dir, model_name, ticker, baseline=False):
    if baseline:
        model_name='plainhist'
    model = np.load(
        os.path.join(model_dir, model_name+'.'+ticker+'.npy'))
    model_meta=cfgparser.read_cfg(os.path.join(model_dir, model_name+'.'+ticker+'.ini'))
    return model, model_meta

def savmatR(oculus):
    model_name=oculus.cfg['PREDICTOR']['model_name']
    ticker=oculus.ticker
    archive_dir=oculus.archive_dir
    np.save(os.path.join(archive_dir,model_name+'.'+ticker+'.npy'), oculus.model)
    cfgparser.write_cfg(
        oculus.cfg, os.path.join(archive_dir,model_name+'.'+ticker+'.ini'))
    utils.write_log(f'{print_prefix}{model_name} for {ticker} Archive Done!')



# ---Unit test---
if __name__ == '__main__':
    pass