#/usr/bin/env python3
''' KERNEL MODULE FOR STRATEGY'''

print_prefix='strategy.minerva>>'

# ---imports---
from ..lib import utils
import datetime
import pandas as pd
class Minerva:
    '''
    minerva engine: strategy implementation engine
    '''
    def __init__(self, cfg):
        self.cfg=cfg
        self.scheme_name=cfg['SCHEMER']['scheme_name']
        self.init_fund=float(cfg['SCHEMER']['init_fund'])
        self.ref_span=utils.cal_trade_day(cfg['SCHEMER']['ref_span'])
        self.rebalance_frq=utils.cal_trade_day(cfg['SCHEMER']['rebalance_frq'])

        self.portfolio=cfg['SCHEMER']['portfolio'].split(',')
        self._load_portfolio()

        if cfg['SCHEMER'].getbool('backtest_flag'):
            self.backtest_start_time=utils.parse_intime(
                self.cfg['SCHEMER']['backtest_start_time'])     
            backtest_end_time=utils.parse_intime(
                self.cfg['SCHEMER']['backtest_end_time'])
            if backtest_end_time =='0':
                self.backtest_end_time=datetime.datetime.now()
            self.backtest_dateseries=pd.date_range(
                start=self.backtest_start_time,
                end=self.backtest_end_time)
        else:
            self.realtime()
   
    def backtest():
        '''
        '''
        for date in self.backtest_dateseries:
            self._feedinfo(date)
    def feedinfo():
        pass
    def realtime():
        pass

    def event_process():
        '''
        listen to events: 
        1. funding signal
        2. trade signal
        3. rebalance signal
        '''
        pass

    def position_manage():
        '''
        '''
        pass

    def risk_manage():
        '''
        '''
        pass
# ---Module regime consts and variables---


# ---Classes and Functions---


# ---Unit test---
if __name__ == '__main__':
    pass
