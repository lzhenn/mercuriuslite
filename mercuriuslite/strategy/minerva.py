#/usr/bin/env python3
''' KERNEL MODULE FOR STRATEGY'''

print_prefix='strategy.minerva>>'

# ---imports---
from ..lib import utils, io, const, painter, mathlib
from ..eval import iustitia
from . import scheme_zoo
import datetime
import numpy as np
import pandas as pd

# ---Module regime consts and variables---
# no risk daily return
NRDR=mathlib.ar2dr(const.NO_RISK_RETURN)

# ---Classes and Functions---

class Minerva:
    '''
    minerva engine: strategy implementation engine
    '''
    def __init__(self, cfg):
        self.cfg=cfg
        self.scheme_name=cfg['SCHEMER']['scheme_name']
        self.strategy = getattr(scheme_zoo, self.scheme_name)
        self.pos_scheme_name=cfg['SCHEMER']['pos_scheme_name']
        self.pos_scheme= getattr(scheme_zoo, 'pos_'+self.pos_scheme_name)
        self.fund_scheme_name=cfg['SCHEMER']['fund_scheme_name']
        self.fund_scheme= getattr(scheme_zoo, 'fund_'+self.fund_scheme_name)
        self.init_fund=float(cfg['SCHEMER']['init_fund'])
        self.db_path=cfg['SCHEMER']['db_path']
        self.baseticker=cfg['SCHEMER']['baseticker']
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
            self.backtest_end_time=utils.parse_intime(
                self.cfg['SCHEMER']['backtest_end_time'])
            if self.backtest_end_time =='0':
                self.backtest_end_time=datetime.datetime.now()
            self.dateseries=pd.date_range(
                start=self.backtest_start_time,
                end=self.backtest_end_time)
        
        # cash flow        
        self.cash_flow=float(cfg['SCHEMER']['cash_flow'])
        self.cash_dates=utils.gen_date_intervals(
            self.dateseries, cfg['SCHEMER']['cash_frq'])
        
        # rebalance
        self.balance_dates=utils.gen_date_intervals(
            self.dateseries, cfg['SCHEMER']['rebalance_frq'])
        self.defer_balance=False
    
    def _load_portfolio(self):
        self.port_hist, self.port_model, self.port_meta={},{},{}
        for tgt, model_name in zip(self.port_tgts,self.model_names):
            utils.write_log(f'{print_prefix}load {tgt}')
            self.port_hist[tgt]=io.load_hist(self.db_path, tgt)
            self.port_model[tgt], self.port_meta[tgt]=io.load_model(
                self.model_path, model_name, tgt, baseline=False)
        self.trading_dates=self.port_hist[self.port_tgts[0]].index
        self.basehist=io.load_hist(self.db_path, self.baseticker)
        self.basehist['drawdown'] = (
            self.basehist['Close'].cummax() - self.basehist['Close']) / self.basehist['Close'].cummax()
    def backtest(self):
        '''
        '''
        start_day=self.backtest_start_time
        end_day=self.backtest_end_time
        utils.write_log(
            f'{print_prefix}{const.HLINE}BACKTESTING: {start_day.strftime("%Y-%m-%d")} START{const.HLINE}')
        self._init_portfolio()
        # backtrace
        for date in self.dateseries:
            self._event_process(date)
        utils.write_log(
            f'{print_prefix}{const.HLINE}BACKTESTING: {end_day.strftime("%Y-%m-%d")} END{const.HLINE}')
        self.inspect()

    def inspect(self):
        '''
        inspect portfolio
        '''
        utils.write_log(f'{print_prefix}inspect portfolio...')
        track=self.track
        track['fund_change']=(track['total_value']-track['accu_fund'])/track['accu_fund']
        track['drawdown'].where(
            track['drawdown']>-track['fund_change'], other=-track['fund_change'],
            inplace=True)
        
        track['daily_return']=np.log(track['daily_return'])
        track['accum_return']=np.exp(track['daily_return'].cumsum())

        # baseline return
        track['baseline_return']=track['accum_return']
        idx_start=self.basehist.index.searchsorted(self.backtest_start_time)
        idx_end=self.basehist.index.searchsorted(self.backtest_end_time)
        base_value=self.basehist.iloc[idx_start]['Close']
        mkt_value=base_value       
        for date in self.dateseries:
            if date in self.trading_dates:
                mkt_value=self.basehist.loc[date]['Close']
            track.loc[date, 'baseline_return']=mkt_value/base_value
        track['baseline_drawdown'] = (
            track['baseline_return'].cummax() - track['baseline_return']) / track['baseline_return'].cummax()
        
        eval_table=iustitia.strategy_eval(track)
        painter.table_print(eval_table) 
        painter.draw_perform_fig(track, self.scheme_name,self.port_tgts)
    def _init_portfolio(self):
        # build portfolio track
        date_series=self.dateseries
        self.track = pd.DataFrame(
            np.zeros(len(date_series)), index=date_series, columns=['accu_fund'])
        
        self.track['cash']=0.0
        self.track['port_value']=0.0
        self.track['total_value']=0.0
        self.track['norisk_total_value']=0.0
        self.track['daily_return']=1.0
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
        #utils.write_log(f'{print_prefix}-------------BACKTESTING: {date.strftime("%Y-%m-%d")} START-----------')
        self._on_funding(date)
        self._on_trade(date)
        self._on_rebalance(date)
        self._on_rolling(date)
    
    def _on_rebalance(self, date):
        if (date in self.balance_dates) or (self.defer_balance):
            if self.trade_flag:
                port_dic=self.pos_scheme(self, date)
                track_rec=self.track.loc[date]
                port_value=track_rec['port_value']
                for tgt in self.port_tgts:
                    value=track_rec[f'{tgt}_value']
                    self.action_dict[tgt]=port_value*port_dic[tgt]-value
                    utils.write_log(f'{print_prefix}Rebalance signal captured.{tgt}:{utils.fmt_value(port_dic[tgt],vtype="pct")}')
                self.trade(date)
                self.defer_balance=False
            else:
                self.defer_balance=True 
    def _on_funding(self, date):
        if date==self.dateseries[0]:
            utils.write_log(
                f'{print_prefix}Initial funding signal captured:{self.init_fund}USD'+\
                f' on {date.strftime("%Y-%m-%d")}')
            self.track.loc[date, 'cash']=self.init_fund
            self.track.loc[date, 'total_value']=self.init_fund
            self.track.loc[date, 'accu_fund']=self.init_fund
            self.new_fund=True
        elif date in self.cash_dates:
            act_flow=self.fund_scheme(
                self, date)
            self.track.loc[date,'cash']+=act_flow
            self.track.loc[date,'total_value']+=act_flow
            self.track.loc[date,'accu_fund']+=act_flow
            self.new_fund=True
            self.act_fund=act_flow
            utils.write_log(
                f'{print_prefix}Funding signal captured:'+\
                f'{self.track.loc[date,"accu_fund"]}USD (+{act_flow}USD)'+\
                f' on {date.strftime("%Y-%m-%d")}')
    def _on_trade(self, date):
        '''
        '''
        self.trade_flag=True
        if date in self.trading_dates:
            #self._adjust_value('Open', date)
            self.strategy(self, date)
        else:
            #utils.write_log(
            #    f'{print_prefix}Market closed on {date.strftime("%Y-%m-%d")}')
            self.trade_flag=False

    def _on_rolling(self, date): 
        '''
        rolling the whole pipeline 
        wrap the day close and roll to the next day open
        '''
        if self.trade_flag:
            self._adjust_value('Close', date)
        
        track=self.track
        day_total=track.loc[date,'total_value']
        if not(date==self.dateseries[0]):
            yesterday=date+datetime.timedelta(days=-1)
            if date in self.cash_dates:
                in_fund=self.act_fund
                track.loc[date, 'daily_return']=day_total/(track.loc[yesterday,'total_value']+in_fund)
                track.loc[date, 'norisk_total_value']=(
                    track.loc[yesterday, 'norisk_total_value']+in_fund)*NRDR
            else:
                track.loc[date, 'daily_return']=day_total/track.loc[yesterday,'total_value']
                track.loc[date, 'norisk_total_value']=track.loc[yesterday, 'norisk_total_value']*NRDR
        else:
            track.loc[date, 'daily_return']=track.loc[date,'total_value']/self.init_fund
            track.loc[date, 'norisk_total_value']=self.init_fund*NRDR
        
        track['drawdown'] = (
            track['total_value'].cummax() - track['total_value']) / track['total_value'].cummax()
        if not(date==self.dateseries[-1]):
            tmr=date+datetime.timedelta(days=1)
            track.loc[tmr]=track.loc[date]

    def _adjust_value(self, price_type, date):
        '''
        adjust value based on open/low/high/close price
        '''
        track=self.track
        track.loc[date,'port_value']=0.0
        for tgt in self.port_tgts:
            price_rec=self.port_hist[tgt].loc[date]
            price=price_rec[price_type]
            share=track.loc[date,f'{tgt}_share']
            track.loc[date,f'{tgt}_value']=share*price
            track.loc[date,'port_value']+=share*price
        track.loc[date,'cash']=track.loc[date,'cash']*NRDR
        nav=track.loc[date,'port_value']+track.loc[date,'cash']
        track.loc[date,'total_value']=nav

    def trade(self,date):
        '''
        determine exact position change, for input
        action_dict= 
        {'SPY':5000,'SPXL':-1000}
        
        positive for buy, negative for sell 
        '''
        #self.risk_manage(date)

        track=self.track
        #[('SPXL', -Val), ('SPY', Val)]
        act_tgt_lst = sorted(self.action_dict.items(), key=lambda x:x[1])
        for act_tgt in act_tgt_lst:
            tgt,val=act_tgt[0],act_tgt[1]
            price_rec=self.port_hist[tgt].loc[date]
            trade_price=(price_rec['High']+price_rec['Low'])/2
            share, cash_fra=utils.cal_trade(trade_price, val)
            if not(share==0):
                utils.write_log(
                    f'{print_prefix}Trade signal captured:{share:.0f} shares'+\
                    f' of {tgt}@{trade_price:.2f}({share*trade_price:.2f}USD)'+\
                    f' on {date.strftime("%Y-%m-%d")}'
                )
                track.loc[date,f'{tgt}_share']+=share
                track.loc[date,f'{tgt}_value']+=share*trade_price
                track.loc[date,'port_value']+=share*trade_price
                track.loc[date,'cash']-=share*trade_price
        track.loc[date,'total_value']= track.loc[date,'port_value']+track.loc[date,'cash']   
   
    def risk_manage(self,date):
        pass     
    def realtime():
        pass


 


# ---Unit test---
if __name__ == '__main__':
    pass
