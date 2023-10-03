#/usr/bin/env python3
''' KERNEL MODULE FOR STRATEGY'''

print_prefix='strategy.minerva>>'

# ---imports---
from ..lib import utils, io, const, painter, messenger
from ..eval import prudentia 
from . import scheme_zoo 
import datetime
import numpy as np
import pandas as pd

# ---Module regime consts and variables---
# no risk daily return

# ---Classes and Functions---

class Minerva:
    '''
    minerva engine: strategy implementation engine
    '''
    def __init__(self, mercurius):
        self.cfg=mercurius.cfg
        cfg=self.cfg
        self.scheme_name=cfg['SCHEMER']['scheme_name']
        self.strategy = getattr(scheme_zoo, self.scheme_name)
        self.pos_scheme_name=cfg['SCHEMER']['pos_scheme_name']
        self.pos_scheme= getattr(scheme_zoo, 'pos_'+self.pos_scheme_name)
        self.fund_scheme_name=cfg['SCHEMER']['fund_scheme_name']
        self.fund_scheme= getattr(scheme_zoo, 'fund_'+self.fund_scheme_name)
        self.cash_scheme_name=cfg['SCHEMER']['cash_scheme_name']
        self.cash_scheme= getattr(scheme_zoo, 'cash_'+self.cash_scheme_name)
        self.norisk_scheme_name=cfg['SCHEMER']['norisk_scheme_name']
        self.norisk_scheme = getattr(scheme_zoo, 'norisk_'+self.norisk_scheme_name)
        self.init_fund=float(cfg['SCHEMER']['init_fund'])
        self.db_path=mercurius.ltm_dir
        self.baseticker=cfg['SCHEMER']['baseticker']
        self.model_path=mercurius.model_path
        self.port_tgts=cfg['SCHEMER']['port_tgts'].replace(' ','').split(',')
       
        self.action_dict={}
        for tgt in self.port_tgts:
            self.action_dict[tgt]=0.0

        self.model_names=cfg['SCHEMER']['port_models'].replace(' ','').split(',')

        if cfg['SCHEMER'].getboolean('backtest_flag'):
            self.scheme_start_time=utils.parse_intime(
                self.cfg['SCHEMER']['scheme_start_time'])     
            self.scheme_end_time=utils.parse_endtime(
                self.cfg['SCHEMER']['scheme_end_time'])
            self.forward_flag=False
            self.real_prefix=''
        elif cfg['SCHEMER'].getboolean('forward_flag'):
            self.forward_flag=True
            self.real_prefix='[REAL]'
            self.real_acc=io.load_real_acc(self.cfg['SCHEMER']['real_acc_file'])
            
            self.scheme_start_time=utils.parse_intime(
                self.cfg['SCHEMER']['scheme_start_time'])     
            if self.scheme_start_time =='0':
                self.scheme_start_time=self.real_acc.loc[0, 'Date']
        
            self.scheme_end_time=utils.parse_endtime(
                    self.cfg['SCHEMER']['scheme_end_time'])
        else:
            utils.throw_error(f'{print_prefix}Either backtest or forward flag set to True')
        
        self.msg_dic=utils.construct_msg(self.scheme_name, self.scheme_end_time)
        
        self.dateseries=pd.date_range(
            start=self.scheme_start_time,
            end=self.scheme_end_time)
        
        self._load_portfolio()
        
        self.eval_dic,self.lastday_dic={},{}
        
        # cash flow        
        self.cash_flow=float(cfg['SCHEMER']['cash_flow'])
        if self.forward_flag or self.cash_flow=='real':
            self.real_cash_dates=utils.real_acc_dates(self.real_acc,'cash')
            #self.cash_dates=self.real_cash_dates
        self.cash_dates=utils.gen_date_intervals(
            self.dateseries, cfg['SCHEMER']['cash_frq'])

        # rebalance
        self.balance_dates=utils.gen_date_intervals(
            self.dateseries, cfg['SCHEMER']['rebalance_frq'])
        # LZN Debug
        self.balance_dates.append(self.scheme_end_time)
        self.defer_balance=False
       
        # no risk
        if self.norisk_scheme_name=='dynamic':
            self.noriskhist=io.load_hist(self.db_path, '^IRX')
        # operation records
        self.operation_df=utils.init_operation_df()
            
    def _load_portfolio(self):
        self.port_hist, self.port_model, self.port_meta={},{},{}
        for tgt, model_name in zip(self.port_tgts,self.model_names):
            utils.write_log(f'{print_prefix}load {tgt}')
            self.port_hist[tgt]=io.load_hist(self.db_path, tgt,add_pseudo=True)
            #self.port_model[tgt], self.port_meta[tgt]=io.load_model(
            #    self.model_path, model_name, tgt, baseline=False)
        trading_dates=self.port_hist[self.port_tgts[0]].index
        idx_start=trading_dates.searchsorted(self.scheme_start_time)
        self.trading_dates=trading_dates[idx_start:]
        self.basehist=io.load_hist(self.db_path, self.baseticker, add_pseudo=True)
        self.basehist['drawdown'] = (
            self.basehist['Close'].cummax() - self.basehist['Close']) / self.basehist['Close'].cummax()
    def account_evolve(self):
        '''
        account track evolve in either backtesting or forward evolving mode
        '''
        start_day=self.scheme_start_time
        end_day=self.scheme_end_time
        
        utils.write_log(
            f'{print_prefix}{const.HLINE}{self.real_prefix}ACCOUNT EVOLVE: {start_day.strftime("%Y-%m-%d")} START{const.HLINE}')
        self._init_portfolio()
        
        # -----------------backtrace-------------------
        for date in self.dateseries:
            self._event_process(date)
        
        utils.write_log(
            f'{print_prefix}{const.HLINE}{self.real_prefix}ACCOUNT EVOLVE: {end_day.strftime("%Y-%m-%d")} END{const.HLINE}')
        
        # inspect portfolio track
        self.inspect()
        if self.forward_flag:
            self.inspect(track_mark='real')
            self.msg_handler()
        self.operation_df.to_csv(
            self.cfg['SCHEMER']['out_operation_file'], index=False)
        
    def msg_handler(self):
        
        # portfolio performance
        tb_msg=painter.dic2html(self.eval_dic)
        self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>Portfolio Performance</h2>{tb_msg}') 
        
        self._parse_ticker_perform()

        # last day status
        tb_msg=painter.dic2html(self.lastday_dic)
        self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>Last Day Status</h2>{tb_msg}')
 
        # ticker details
        tb_msg=painter.dic2html(self.ticker_perform_dic)
        self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>Ticker Performance Details</h2>{tb_msg}')
       
        title, content=utils.form_msg(self.msg_dic)
        io.archive_msg(self.cfg['SCHEMER']['out_msg_file'], title, content)
        
        if self.cfg['SCHEMER'].getboolean('send_msg'):
            messenger.gmail_send_message(self.cfg, title, content)
    
    def inspect(self,track_mark=None):
        '''
        inspect portfolio
        '''
        if track_mark is None:
            track=self.track
            track_identity='Scheme Account'
            fig_fn=utils.form_scheme_fig_fn(self.cfg)
        else:
            track=self.real_track
            track_identity='Real Account'
            fig_fn=utils.form_scheme_fig_fn(self.cfg,suffix='real')
        utils.write_log(f'{print_prefix}{track_identity} inspect portfolio...')
        track=prudentia.track_inspect(track)
        track['drawdown'].where(
            track['drawdown']>-track['fund_change'], other=-track['fund_change'],
            inplace=True)

        # baseline return
        track['baseline_return']=track['accum_return']
        idx_start=self.basehist.index.searchsorted(self.scheme_start_time)
        base_value=self.basehist.iloc[idx_start]['Close']
        mkt_value=base_value       
        for date in self.dateseries:
            if date in self.trading_dates:
                mkt_value=self.basehist.loc[date]['Close']
            track.loc[date, 'baseline_return']=mkt_value/base_value
        track['baseline_drawdown'] = (
            track['baseline_return'].cummax() - track['baseline_return']) / track['baseline_return'].cummax()
        
        # portfolio performance table
        eval_table=prudentia.strategy_eval(track)
        #tb_msg=painter.table_print(eval_table,table_fmt='html')
        self.eval_dic=painter.append_dic_table(
            self.eval_dic, eval_table, 
            column_name=track_identity, index_name='Metrics')
       # last day track
        lstday_dic=track.iloc[-1].to_dict()
        lstday_dic['accum_return']=lstday_dic['accum_return']-1
        lstday_dic['baseline_return']=lstday_dic['baseline_return']-1
        lstday_dic['drawdown']=-lstday_dic['drawdown'] 
        lstday_dic['baseline_drawdown']=-lstday_dic['baseline_drawdown'] 
        lstday_dic=painter.fmt_dic(lstday_dic)
        self.lastday_dic=painter.append_dic_table(
            self.lastday_dic, lstday_dic,
            column_name=track_identity, index_name='Metrics')
        painter.draw_perform_fig(track, self.port_tgts, fig_fn)
        #print(track.iloc[-1])
    def _event_process(self, date):
        '''
        listen to events: 
        1. funding signal
        2. trade signal
        3. rebalance signal
        '''
        #utils.write_log(f'{print_prefix}-------------BACKTESTING: {date.strftime("%Y-%m-%d")} START-----------')
        self._on_kickoff(date)
        self._on_funding(date)
        self._on_rebalance(date)
        self._on_trade(date)
        self._on_rolling(date)
        if self.forward_flag:
            self._on_rolling(date,track_mark='real')

    def _init_portfolio(self):
        # build portfolio track
        date_series=self.dateseries
        self.track = utils.init_track(date_series, self.port_tgts)
        if self.forward_flag:
            self.real_track=utils.init_track(date_series, self.port_tgts)

    def _on_kickoff(self, date):
        self.NRDR=self.norisk_scheme(self,date)

    def _on_rebalance(self, date):
        if (date in self.balance_dates) or (self.defer_balance):
            if date in self.trading_dates:    
                self._rebalance(date)
            else:
                self.defer_balance=True
            # skip this month DCA invest
            self.new_fund=False
    def _rebalance(self,date):
        track_rec=self.track.loc[date]
        utils.write_log(
            f'{print_prefix}[PROPOSED] Rebalance signal captured on {date.strftime("%Y-%m-%d")}.')
        port_dic=self.pos_scheme(self, date)
        total_value=track_rec['total_value']
        for tgt in self.port_tgts:
            value=track_rec[f'{tgt}_value']
            self.action_dict[tgt]=total_value*port_dic[tgt]-value
        # adjust by specific scheme
        self.action_dict=getattr(
            scheme_zoo, self.scheme_name+'_rebalance')(self, date)
        self.trade(date,call_from='Rebalance')
        #print_dic = {k: round(v, 2) for k, v in port_dic.items()}
        #utils.write_log(f'{print_prefix}Rebalanced Portfolio: {print_dic} ')
        self.defer_balance=False 
       
    def _on_trade(self, date):
        if (date in self.trading_dates):
        #if (date in self.trading_dates and self.new_fund):
            self.strategy(self, date)
            if date != self.dateseries[-1]:
                self.new_fund=False
        if self.forward_flag: 
            if date in self.real_acc['Date'].values:
                self._trade_real(date)
            if date == self.dateseries[-1]:
                self.strategy(self, date, track_mark='real')
            
    def _trade_real(self,date):
        track=self.real_track
        real_acc=self.real_acc
        trade_rec=real_acc[real_acc['Date']==date]
        for row in trade_rec.itertuples():
            tgt=row.ticker
            if tgt == 'cash':
                continue
            share=row.share
            trade_price=row.price
            track.loc[date,f'{tgt}_share']+=share
            track.loc[date,f'{tgt}_value']+=share*trade_price
            track.loc[date,'port_value']+=share*trade_price
            track.loc[date,'cash']-=share*trade_price
            track.loc[date,'total_value']= track.loc[date,'port_value']+track.loc[date,'cash']   
            utils.write_log(
                    f'{print_prefix}{self.real_prefix}Trade signal captured:{share:.0f} shares'+\
                    f' of {tgt}@{trade_price:.2f}({share*trade_price:.2f}USD)'+\
                    f' on {date.strftime("%Y-%m-%d")}')
                
    def _on_funding(self, date):
        if date==self.dateseries[0]:
            act_flow=self.init_fund
        elif date in self.cash_dates:
            act_flow=self.fund_scheme(self, date)
        elif date == self.dateseries[-1] and date.day==1:
            act_flow=scheme_zoo.fund_fixed(self, date)
            self.msg_dic=utils.feed_msg_title(self.msg_dic, 'CASH_IN'+utils.fmt_value(act_flow))
            msg=f'***CASH_IN***Funding signal captured, current fund:'+\
                f'{utils.fmt_value(self.real_track.loc[date,"accu_fund"])} (+{utils.fmt_value(act_flow)})'+\
                f' on {date.strftime("%Y-%m-%d")}'
            utils.write_log(print_prefix+msg)
            self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>{msg}</h2>')
        else:
            return
        
        self._feed_operation(date, 'cash', np.nan, act_flow)
        self.track.loc[date, 'cash']+=act_flow
        self.track.loc[date, 'total_value']+=act_flow
        self.track.loc[date, 'accu_fund']+=act_flow
        
        self.new_fund=True
        # new funding 
        self.act_fund=act_flow
        
        # init trade scheme
        if date==self.dateseries[0]:
            getattr(scheme_zoo, self.scheme_name+'_init')(self, date)
        utils.write_log(
            f'{print_prefix}[PROPOSED] Funding signal captured, current fund:'+\
            f'{utils.fmt_value(self.track.loc[date,"accu_fund"])} (+{utils.fmt_value(act_flow)})'+\
            f' on {date.strftime("%Y-%m-%d")}')
        
        
        if self.forward_flag: 
            if date in self.real_cash_dates:
                real_flow=scheme_zoo.fund_real(self, date)
                self.real_act_fund=real_flow
                self.real_track.loc[date, 'cash']+=real_flow
                self.real_track.loc[date, 'total_value']+=real_flow
                self.real_track.loc[date, 'accu_fund']+=real_flow
                utils.write_log(
                    f'{print_prefix}{self.real_prefix}Funding signal captured, current fund:'+\
                    f'{utils.fmt_value(self.track.loc[date,"accu_fund"])} (+{utils.fmt_value(act_flow)})'+\
                    f' on {date.strftime("%Y-%m-%d")}')
            
    def _feed_operation(self, date, tgt, share, price):
        date=date.strftime("%Y%m%d")
        new_row = {'Date': date, 'ticker': tgt, 'share': share, 'price': price}
        self.operation_df=self.operation_df.append(new_row, ignore_index=True)
    def _on_rolling(self, date, track_mark=None): 
        '''
        rolling the whole pipeline 
        wrap the day close and roll to the next day open
        '''
        if track_mark is None:
            track=self.track
            cash_dates=self.cash_dates
            ini_fund=self.init_fund
        else:
            track=self.real_track
            cash_dates=self.real_cash_dates
            ini_fund=self.fund_scheme(self, cash_dates[0])
        if date in self.trading_dates:    
            self._adjust_value(track, 'Close', date)
        
        day_total=track.loc[date,'total_value']
        if not(date==self.dateseries[0]):
            yesterday=date+datetime.timedelta(days=-1)

            if date in cash_dates:
                in_fund=self.act_fund
                track.loc[date, 'daily_return']=day_total/(
                    track.loc[yesterday,'total_value']+in_fund)
                track.loc[date, 'norisk_total_value']=(
                    track.loc[yesterday, 'norisk_total_value']+in_fund)*self.NRDR
            else:
                track.loc[date, 'daily_return']=day_total/track.loc[yesterday,'total_value']
                track.loc[date, 'norisk_total_value']=track.loc[yesterday, 'norisk_total_value']*self.NRDR
        else:
            track.loc[date, 'daily_return']=track.loc[date,'total_value']/ini_fund
            track.loc[date, 'norisk_total_value']=ini_fund*self.NRDR
        
        track['drawdown'] = (
            track['total_value'].cummax() - track['total_value']) / track['total_value'].cummax()
        
        if not(date==self.dateseries[-1]):
            tmr=date+datetime.timedelta(days=1)
            track.loc[tmr]=track.loc[date]
    def _adjust_value(self, track, price_type, date):
        '''
        adjust value based on open/low/high/close price
        '''
        track.loc[date,'port_value']=0.0
        for tgt in self.port_tgts:
            price_rec=self.port_hist[tgt].loc[date]
            price=price_rec[price_type]
            share=track.loc[date,f'{tgt}_share']
            track.loc[date,f'{tgt}_value']=share*price
            track.loc[date,'port_value']+=share*price
        track.loc[date,'cash']=track.loc[date,'cash']*self.NRDR
        nav=track.loc[date,'port_value']+track.loc[date,'cash']
        track.loc[date,'total_value']=nav

    def _parse_ticker_perform(self):
        self.ticker_perform_dic={
            'header':['Tickers', 'Price', 'ShortLag', 'LongLag', 'Shares', 'Value',
                      'AccuInflow', 'AccuOutflow', 'CurrReturn']}
        tickers=self.port_tgts
        date_now=self.dateseries[-1]
        op_df, real_acc=self.operation_df, self.real_acc
        for ticker in tickers:
            price_rec=self.port_hist[ticker].loc[date_now]
            price=price_rec['Close']
            lastday_share=self.lastday_dic[f'{ticker}_share']
            lastday_value=self.lastday_dic[f'{ticker}_value']
            in_s, out_s=utils.cal_flow(op_df,ticker)
            gain_s= float(lastday_value[0][1:])-out_s-in_s
            in_r, out_r=utils.cal_flow(real_acc,ticker)
            gain_r= float(lastday_value[1][1:])-out_r-in_r

            (ma_shortlag,shortvalue)=self.ma_cross[f'{ticker}_short']
            (ma_longlag,longvalue)=self.ma_cross[f'{ticker}_long']
            short_str=f'{utils.fmt_value(shortvalue)} (MA{ma_shortlag})'
            long_str=f'{utils.fmt_value(longvalue)} (MA{ma_longlag})'
            self.ticker_perform_dic[f'{ticker} (S)']=[
                utils.fmt_value(price),short_str, long_str,
                lastday_share[0], lastday_value[0], 
                utils.fmt_value(in_s), utils.fmt_value(out_s),
                utils.fmt_value(gain_s)]
            self.ticker_perform_dic[f'{ticker} (R)']=[
                utils.fmt_value(price), short_str, long_str,
                lastday_share[1], lastday_value[1], 
                utils.fmt_value(in_r), utils.fmt_value(out_r),
                utils.fmt_value(gain_r)]
            self.lastday_dic.pop(f'{ticker}_share')
            self.lastday_dic.pop(f'{ticker}_value')
        #exit()
    def trade(self, date, call_from='DCA', price_type='NearOpen', track_mark=None):
        '''
        determine exact position change, for input
        action_dict= 
        {'SPY':5000,'SPXL':-1000}
        
        positive for buy, negative for sell 
        '''
        #self.risk_manage(date)
        if track_mark is None:
            track=self.track
            msg_prefix='[PROPOSED]'
        else:
            track=self.real_track
            self.msg_dic=utils.feed_msg_title(self.msg_dic, call_from)
            msg_prefix='[REAL]'
        #[('SPXL', -Val), ('SPY', Val)]
        act_tgt_lst = sorted(self.action_dict.items(), key=lambda x:x[1])
        for act_tgt in act_tgt_lst:
            tgt,val=act_tgt[0],act_tgt[1]
            price_rec=self.port_hist[tgt].loc[date]
            trade_price=utils.determ_price(price_rec, price_type)
            share, cash_fra=utils.cal_trade(trade_price, val)
            if not(share==0):
                log_data=f'{msg_prefix}**{call_from}**Trade signal captured:{share:.0f} shares'+\
                    f' of {tgt}@{trade_price:.2f}({share*trade_price:.2f}USD)'+\
                    f' on {date.strftime("%Y-%m-%d")}'
                if track_mark=='real':
                    self.msg_dic=utils.feed_msg_title(self.msg_dic, f'{tgt}:{share:.0f}@{trade_price:.2f}')
                    self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>{log_data}</h2>')
                utils.write_log(print_prefix+log_data)

                track.loc[date,f'{tgt}_share']+=share
                track.loc[date,f'{tgt}_value']+=share*trade_price
                track.loc[date,'port_value']+=share*trade_price
                track.loc[date,'cash']-=share*trade_price
                self._feed_operation(date, tgt, share, trade_price)
        track.loc[date,'total_value']= track.loc[date,'port_value']+track.loc[date,'cash']   

            
# ---Unit test---
if __name__ == '__main__':
    pass
