#/usr/bin/env python3
''' KERNEL MODULE FOR STRATEGY'''

print_prefix='strategy.minerva>>'

# ---imports---
from ..lib import utils, io
from . import zoo
import datetime
import numpy as np
import pandas as pd
class Minerva:
    '''
    minerva engine: strategy implementation engine
    '''
    def __init__(self, cfg):
        self.cfg=cfg
        self.scheme_name=cfg['SCHEMER']['scheme_name']
        self.strategy = getattr(zoo, self.scheme_name)
        self.init_fund=float(cfg['SCHEMER']['init_fund'])
        self.ref_span=utils.cal_trade_day(cfg['SCHEMER']['ref_span'])
        self.rebalance_frq=utils.cal_trade_day(cfg['SCHEMER']['rebalance_frq'])
        self.db_path=cfg['SCHEMER']['db_path']
        self.model_path=cfg['SCHEMER']['model_path']
        self.port_tgts=cfg['SCHEMER']['port_tgts'].replace(' ','').split(',')
        
        self.action_dict={}
        for tgt in self.port_tgts:
            self.action_dict[tgt]=0.0

        self.model_names=cfg['SCHEMER']['port_models'].replace(' ','').split(',')
        self._load_portfolio()

        if cfg['SCHEMER'].getboolean('backtest_flag'):
            self.backtest_start_time=utils.parse_intime(
                self.cfg['SCHEMER']['backtest_start_time'])     
            backtest_end_time=utils.parse_intime(
                self.cfg['SCHEMER']['backtest_end_time'])
            if backtest_end_time =='0':
                self.backtest_end_time=datetime.datetime.now()
            self.dateseries=pd.date_range(
                start=self.backtest_start_time,
                end=self.backtest_end_time)
        # cash flow        
        self.cash_flow=float(cfg['SCHEMER']['cash_flow'])
        self.cash_dates=utils.gen_date_intervals(
            self.dateseries, cfg['SCHEMER']['cash_frq'])
    def _load_portfolio(self):
        self.port_hist, self.port_model, self.port_meta={},{},{}
        for tgt, model_name in zip(self.port_tgts,self.model_names):
            utils.write_log(f'{print_prefix}load {tgt}')
            self.port_hist[tgt]=io.load_hist(self.db_path, tgt)
            self.port_model[tgt], self.port_meta[tgt]=io.load_model(
                self.model_path, model_name, tgt, baseline=False)
        self.trading_dates=self.port_hist[self.port_tgts[0]].index

    def backtest(self):
        '''
        '''
        self._init_portfolio()
        # backtrace
        for date in self.dateseries:
            self._event_process(date)

        print(self.track)
    def _init_portfolio(self):
        # build portfolio track
        date_series=self.dateseries
        self.track = pd.DataFrame(
            np.zeros(len(date_series)), index=date_series, columns=['accu_fund'])
        
        self.track['cash']=0.0
        self.track['port_value']=0
        
        for ticker in self.port_tgts:
            self.track[f'{ticker}_value']=0.0
            self.track[f'{ticker}_share']=0

    def _feedinfo(self, date):
        self.message={'date':date}
    def _event_process(self, date):
        '''
        listen to events: 
        1. funding signal
        2. trade signal
        3. rebalance signal
        '''
        self._on_funding(date)
        self._on_trade(date)
        self._on_rebalance(date)
        self._on_rolling(date)
    
    def _on_funding(self, date):    
        if date==self.dateseries[0]:
            utils.write_log(
                f'{print_prefix}Initial funding signal captured:{self.init_fund}USD'+\
                f' on {date.strftime("%Y-%m-%d")}')
            self.track.loc[date, 'cash']=self.init_fund
            self.track.loc[date, 'accu_fund']=self.init_fund
        if date in self.cash_dates:
            self.track.loc[date,'cash']+=self.cash_flow
            self.track.loc[date,'accu_fund']+=self.cash_flow
            utils.write_log(
                f'{print_prefix}Funding signal captured:'+\
                f'{self.track.loc[date,"accu_fund"]}USD (+{self.cash_flow}USD)'+\
                f' on {date.strftime("%Y-%m-%d")}')
    def _on_trade(self, date):
        '''
        '''
        if date in self.trading_dates:
            self.strategy(self, date)
        else:
            utils.write_log(
                f'{print_prefix}Market closed on {date.strftime("%Y-%m-%d")}')
        
    def _on_rebalance(self, date):
        pass           

    def _on_rolling(self, date): 
        '''
        rolling the whole pipeline change to next day initial state 
        '''
        if not(date==self.dateseries[-1]):
            tmr=date+datetime.timedelta(days=1)
            self.track.loc[tmr]=self.track.loc[date]


    def pos_manage(self,date):
        '''
        {'SPY':5000, 'QQQ':-1000}
        positive for buy, negative for sell 
        '''
        port_rec=self.track.loc[date]
        cash = port_rec['cash']

 
    def risk_manage(self,date):
        '''
        '''
        pass

    def realtime():
        pass



# ---Module regime consts and variables---


# ---Classes and Functions---


# ---Unit test---
if __name__ == '__main__':
    pass
