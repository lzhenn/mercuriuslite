#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import datetime
from . import utils

# ---Module regime consts and variables---
print_prefix='lib.io>>'

# ---Classes and Functions---
       
def load_xy(Xnames, Yfile, Ytgt, train_start_time, train_end_time):
    
    Y, train_start_time, train_end_time =load_y(
        Yfile, Ytgt, train_start_time, train_end_time)
    
    if Xnames == 'na':
        X = np.zeros(Y.shape)
    else:
        X=load_x(Xnames)
    
    check_xy(X,Y)

    return X, Y, train_start_time, train_end_time
    #self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(
    #        self.X, self.Y, test_size=self.test_size, shuffle=False)
def load_y(Yfile, Ytgt, start_time, end_time, call_from='train'):
    ''' select y according to prescribed method '''
    parser = lambda date: datetime.datetime.strptime(date.split()[0],'%Y-%m-%d')
    lb_all=pd.read_csv(Yfile, 
        parse_dates=True, date_parser=parser, index_col='Date')
    if start_time == '0':
        start_time=lb_all.index[0].strftime('%Y%m%d')
    if end_time == '0':
        end_time=lb_all.index[-1].strftime('%Y%m%d')
    Y=lb_all[Ytgt][start_time:end_time].values
    return Y, start_time, end_time

def load_x(self,call_from='train'):
    ''' load feature lib '''
    parser = lambda date: datetime.datetime.strptime(date, '%Y-%m-%d')
    if call_from == 'train':
        flib_all=pd.read_csv(
                'feature_lib/'+self.feature_lib_file, 
                parse_dates=True, date_parser=parser, index_col='time')
    elif call_from=='cast':
        flib_all=pd.read_csv(
                'inferX/'+self.infer_file, 
                parse_dates=True, date_parser=parser, index_col='time')


    self.select_x(flib_all, call_from)
    
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
        utils.write_log(print_prefix+'Sample Size:'+str(Y.shape))



# ---Unit test---
if __name__ == '__main__':
    pass