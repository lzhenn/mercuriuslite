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
        if self.baseticker=='':
            self.withbase=False
        else:
            self.withbase=True
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
            self.real_prefix='[*REAL_ACCOUNT*]'
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
        self.att_dic={}
        
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
        if not(self.balance_dates==[]):
            self.balance_dates.append(self.scheme_end_time)
        self.defer_balance=False
       
        # no risk
        if self.norisk_scheme_name=='dynamic':
            self.noriskhist=io.load_hist(self.db_path, '^IRX_daily',add_pseudo=True)
        # operation records
        self.operation_df=utils.init_operation_df()
        
        # financing account
        if self.fund_scheme_name=='financing':
            self.meta_dic=io.load_msg('financing_meta.json')
            scheme_zoo.fund_financing_init(self)        
        
        # leverage
        self.lev_flag=False
        self.lev_fund_flow=0.0
        self.lev_ratio=1.0
        if self.cfg.has_option('SCHEMER','use_leverage'):
            self.lev_flag=self.cfg['SCHEMER'].getboolean('use_leverage')
            if self.lev_flag:
                self.lev_scheme_name=cfg['LEVERAGE']['lev_scheme_name']
                self.lev_scheme = getattr(scheme_zoo, 'lev_'+self.lev_scheme_name)
                self.lev_ratio=float(cfg['LEVERAGE']['lev_ratio'])/100
                self.lev_flow=float(cfg['LEVERAGE']['flow'])
                self.lev_interest_name=cfg['LEVERAGE']['interest_scheme'] 
                self.lev_interest_scheme = getattr(scheme_zoo, 'lev_interest_'+self.lev_interest_name)
                self.lev_acc_fund=0.0
                self.lev_acc_paid=0.0
                self.lev_acc_unpaid=0.0
                self.lev_dates=utils.gen_date_intervals(
                    self.dateseries, cfg['LEVERAGE']['lev_frq'])
  
                self.lev_interest_dates=utils.gen_date_intervals(
                    self.dateseries, cfg['LEVERAGE']['interest_pay_frq'])

    def _load_portfolio(self):
        self.port_hist, self.port_model, self.port_meta={},{},{}
        for tgt, model_name in zip(self.port_tgts,self.model_names):
            self.port_hist[tgt]=io.load_hist(self.db_path, tgt,add_pseudo=self.forward_flag)
            #self.port_model[tgt], self.port_meta[tgt]=io.load_model(
            #    self.model_path, model_name, tgt, baseline=False)
        trading_dates=self.port_hist[self.port_tgts[0]].index
        idx_start=trading_dates.searchsorted(self.scheme_start_time)
        self.trading_dates=trading_dates[idx_start:]
        if self.withbase:
            self.basehist=io.load_hist(self.db_path, self.baseticker, add_pseudo=self.forward_flag)
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
         
        # -----------------!!!BACKTRACE KERNEL!!!-------------------
        for date in self.dateseries:
            self._event_process(date)
            if self.bankruptcy_flag:
                return
       # -----------------!!!BACKTRACE KERNEL!!!-------------------
        
        utils.write_log(
            f'{print_prefix}{const.HLINE}{self.real_prefix}ACCOUNT EVOLVE: {end_day.strftime("%Y-%m-%d")} END{const.HLINE}')
        
        # inspect portfolio track
        self.inspect()
        if self.forward_flag:
            self.inspect(track_mark='real')
            self.msg_handler()
        if self.fund_scheme_name=='financing':
            self.financing_msg_hdler()
        self.operation_df.to_csv(
            self.cfg['SCHEMER']['out_operation_file'], index=False)
    
    def _init_portfolio(self):
        # build portfolio track
        date_series=self.dateseries
        self.track = utils.init_track(date_series, self.port_tgts)
        if self.forward_flag:
            self.real_track=utils.init_track(date_series, self.port_tgts)

        self.bankruptcy_flag=False
            
    def _event_process(self, date):
        '''
        listen to events: 
        1. funding signal
        2. trade signal
        3. rebalance signal
        '''
        #utils.write_log(f'{print_prefix}-------------BACKTESTING: {date.strftime("%Y-%m-%d")} START-----------')
        self._on_kickoff(date)
        self._on_leverage(date)
        self._on_funding(date)
        self._on_rebalance(date)
        self._on_trade(date)
        self._on_rolling(date)
        if self.forward_flag:
            self._on_rolling(date,track_mark='real')

    def _on_kickoff(self, date):
        # daily kickoff signal
        self.NRDR=self.norisk_scheme(self,date)
    
    def _on_leverage(self, date):
        if not(self.lev_flag):
            return
        if date==self.dateseries[0]:
            self.lev_acc_fund=scheme_zoo.leverage_init(self, self.lev_scheme_name)
            self.lev_fund_flow=self.lev_acc_fund
            self.track.loc[date,'lev_value']=self.lev_acc_fund
            utils.write_log(f'{print_prefix}[ON_LEVERAGE] -!LEVERAGED STRATEGY!- ratio: {utils.fmt_value(self.lev_ratio,"pct",False)},'+\
                f'fund: {utils.fmt_value(self.lev_acc_fund,pos_sign=False)}.')
        else:
            yesterday=date+datetime.timedelta(days=-1)
            ir=self.lev_interest_scheme(self, date)
            self.track.loc[date, 'lev_value']=self.track.loc[yesterday, 'lev_value']*ir
            self.lev_acc_unpaid+=self.track.loc[date, 'lev_value']-self.track.loc[yesterday, 'lev_value']
            self.lev_fund_flow=0.0
            
        if date in self.lev_dates: # leverage inflow
            flow=self.lev_scheme(self, date)
            self.lev_fund_flow=flow
            if flow>0:
                self.new_fund=True    
                self.lev_acc_fund+=flow
                for itm in ['cash','lev_value','accu_fund','total_value']:
                    self.track.loc[date, itm]+=flow
                self._feed_operation(date, 'cash', np.nan, flow)
                lr=self.track.loc[date,'total_value']/self.track.loc[date,'net_value']
                utils.write_log(
                    f'{print_prefix}[ON_LEVERAGE] Financing flow signal captured,'+\
                    f' flow:{utils.fmt_value(flow,pos_sign=False)},'+\
                    f' total flow:{utils.fmt_value(self.lev_acc_fund,pos_sign=False)},'+\
                    f' leveraged fund:{utils.fmt_value(self.track.loc[date,"lev_value"])} ({utils.fmt_value(lr,"pct")})'+\
                    f' on {date.strftime("%Y-%m-%d")}')  
        if date in self.lev_interest_dates: # pay interest
            if self.track.loc[date, 'cash']<self.lev_acc_unpaid:
                self._adjust_value(self.track, 'Open', date)
                if self.track.loc[date, 'total_value']>self.lev_acc_unpaid:
                    self._force_sell(date, self.lev_acc_unpaid)
                else:                    
                    self.bankruptcy_flag=True
                    utils.write_log(f'{print_prefix}[ON_LEVERAGE]**!!!BANKRUPTCY!!!** Unable to pay leverage interest'+\
                        f'{utils.fmt_value(self.lev_acc_unpaid)} on {date.strftime("%Y-%m-%d")}.')
                    return
            for itm in ['cash','lev_value','accu_fund','total_value']:
                self.track.loc[date, itm]-=self.lev_acc_unpaid
            self.lev_acc_paid+=self.lev_acc_unpaid
            self._feed_operation(date, 'cash', np.nan, self.lev_acc_unpaid) 
            lr=self.track.loc[date,'total_value']/self.track.loc[date,'net_value']
            utils.write_log(
                f'{print_prefix}[ON_LEVERAGE] Interest payment signal captured,'+\
                f' pay:{utils.fmt_value(self.lev_acc_unpaid,pos_sign=False)},'+\
                f' total paid:{utils.fmt_value(self.lev_acc_paid,pos_sign=False)},'+\
                f' leveraged fund:{utils.fmt_value(self.track.loc[date,"lev_value"])} ({utils.fmt_value(lr,"pct")})'+\
                f' on {date.strftime("%Y-%m-%d")}')             
            self.lev_acc_unpaid=0.0

    def _on_funding(self, date):
        act_flow=0
        
        if date==self.dateseries[0]:
            act_flow=self.init_fund
            getattr(scheme_zoo, self.scheme_name+'_init')(self, date)
            self.new_fund=True
            self.acc_act_fund=act_flow/self.lev_ratio
            self.acc_out_fund=0.0
        # financing account, could deposit/withdraw anytime
        elif self.fund_scheme_name=='financing':
            act_flow=self.fund_scheme(self, date)
        elif date in self.cash_dates:
            act_flow=self.fund_scheme(self, date)
            self.new_fund=True
            # accumulate new funding
            self.acc_act_fund+=max(act_flow,0)
         
        if act_flow<0:
            if  self.track.loc[date, 'cash']+act_flow<0:
                self._adjust_value(self.track, 'Open', date)
                if self.track.loc[date, 'total_value']>abs(act_flow):
                    self._force_sell(date, abs(act_flow))
                else:
                    self.bankruptcy_flag=True
                    utils.write_log(f'{print_prefix}[ON_FUNDING]**!!!BANKRUPTCY!!!** Unable to pay periodic outflow funding'+\
                        f'{utils.fmt_value(act_flow)} on {date.strftime("%Y-%m-%d")}.')
                    return
            self.acc_out_fund+=act_flow
        # new funding 
        self.act_fund_flow=act_flow
       
        if act_flow!=0:
            # deal with new funding 
            self.track.loc[date, 'cash']+=act_flow
            self.track.loc[date, 'total_value']+=act_flow
            self.track.loc[date, 'accu_fund']+=act_flow
            self._feed_operation(date, 'cash', np.nan, act_flow)
            
            msg_log=f'[ON_FUNDING] Funding signal captured, current fund:'+\
                f'{utils.fmt_value(self.track.loc[date,"accu_fund"],pos_sign=False)} ({utils.fmt_value(act_flow,pos_sign=False)})'+\
                f', cash left: {utils.fmt_value(self.track.loc[date,"cash"],pos_sign=False)} on {date.strftime("%Y-%m-%d")}'
            utils.write_log(print_prefix+msg_log)
        
        # deal with real account
        if self.forward_flag:
            self.real_act_fund_flow=0
            # forward feed lastday msg
            if date==self.dateseries[-1] and self.new_fund:
                self.msg_dic=utils.feed_msg_title(
                    self.msg_dic, 'CASH_INOUT'+utils.fmt_value(act_flow))
                self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>{msg_log}</h2>')
 
            if date in self.real_cash_dates:
                real_flow=scheme_zoo.fund_real(self, date)
                self.real_act_fund_flow=real_flow
                self.real_track.loc[date, 'cash']+=real_flow
                self.real_track.loc[date, 'total_value']+=real_flow
                self.real_track.loc[date, 'accu_fund']+=real_flow
                utils.write_log(
                    f'{print_prefix}{self.real_prefix}Funding signal captured, current fund:'+\
                    f'{utils.fmt_value(self.real_track.loc[date,"accu_fund"])} (+{utils.fmt_value(real_flow)})'+\
                    f' on {date.strftime("%Y-%m-%d")}')
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
            f'{print_prefix}[ON_REBALANCE] Rebalance signal captured on {date.strftime("%Y-%m-%d")}.')
        port_dic=self.pos_scheme(self, date)
        total_value=track_rec['total_value']
        for tgt in self.port_tgts:
            value=track_rec[f'{tgt}_value']
            self.action_dict[tgt]=total_value*port_dic[tgt]-value
        # adjust by specific scheme
        self.action_dict=getattr(
            scheme_zoo, self.scheme_name+'_rebalance')(self, date)
        self.trade(date,call_from='REBALANCE')
        #print_dic = {k: round(v, 2) for k, v in port_dic.items()}
        #utils.write_log(f'{print_prefix}Rebalanced Portfolio: {print_dic} ')
        self.defer_balance=False 
       
    def _on_trade(self, date):
        if (date in self.trading_dates):
            self.strategy(self, date) # even without newfund, strategy-based trading exists 
            self.new_fund=False
        if self.forward_flag: 
            if date in self.real_acc['Date'].values:
                self.trade_real(date)
           
    def _feed_operation(self, date, tgt, share, price):
        '''feed operation to operation dataframe'''
        date=date.strftime("%Y%m%d")
        new_row = {'Date': date, 'ticker': tgt, 'share': share, 'price': price}
        self.operation_df=self.operation_df.append(new_row, ignore_index=True)
    
    def _on_rolling(self, date, track_mark=None): 
        '''
        rolling the whole pipeline 
        wrap the day close and roll to the next day open
        '''
        yesterday=date+datetime.timedelta(days=-1)
        if track_mark is None:
            track=self.track
            cash_dates=self.cash_dates
            ini_fund=self.init_fund
        else:
            track=self.real_track
            cash_dates=self.real_cash_dates
            ini_fund=self.fund_scheme(self, cash_dates[0])
        self._adjust_value(track, 'Close', date)
        
        
               
        day_total=track.loc[date,'total_value']
        day_lev=track.loc[date,'lev_value']
        track.loc[date,'net_value']=day_total-day_lev
        day_net=track.loc[date,'net_value']
        
        # add leveraged tickers to calculate leverage ratio
        lev_tikcer_value=0
        for tgt in self.port_tgts:
            if tgt in const.LEV_TICKERS:
                lev_port=(const.LEV_TICKERS[tgt]-1.0)
                lev_tikcer_value+=lev_port*track.loc[date,f'{tgt}_value']
        track.loc[date,'lev_ratio']=(day_total+lev_tikcer_value)/day_net


        if (date==self.dateseries[0]):
            track.loc[date, 'daily_return']=day_total/ini_fund
            track.loc[date,'daily_net_return']=(day_total-day_lev)/day_net
            track.loc[date, 'norisk_total_value']=ini_fund*self.NRDR
        else:
            if track_mark is None:
                in_fund=self.act_fund_flow+self.lev_fund_flow # 0 in non-funding day
                net_fund=self.act_fund_flow
            else:
                in_fund=self.real_act_fund_flow
                net_fund=in_fund
            
            track.loc[date, 'daily_return']=day_total/(track.loc[yesterday,'total_value']+in_fund)
            track.loc[date,'daily_net_return']=(day_net/(track.loc[yesterday,'net_value']+net_fund))
            track.loc[date, 'norisk_total_value']=(
            track.loc[yesterday, 'norisk_total_value']+in_fund)*self.NRDR
            track['drawdown'] = (
            track['total_value'].cummax() - track['total_value']) / track['total_value'].cummax()
        track['net_drawdown'] = (
            track['net_value'].cummax() - track['net_value']) / track['net_value'].cummax()
        if day_net < 0: 
            self.bankruptcy_flag=True
            utils.write_log(f'{print_prefix}[ON_ROLLING]**!!!BANKRUPTCY!!!** NAV: {utils.fmt_value(day_net)} on {date.strftime("%Y-%m-%d")}')
            return
        if not(date==self.dateseries[-1]):
            tmr=date+datetime.timedelta(days=1)
            track.loc[tmr]=track.loc[date]
    def _adjust_value(self, track, price_type, date):
        '''
        adjust value based on open/low/high/close price
        '''
        trade_day=utils.find_trade_date(date, self.trading_dates)
        track.loc[date,'port_value']=0.0
        for tgt in self.port_tgts:
            price_rec=self.port_hist[tgt].loc[trade_day]
            price=price_rec[price_type]
            share=track.loc[date,f'{tgt}_share']
            track.loc[date,f'{tgt}_value']=share*price
            track.loc[date,'port_value']+=share*price
        if price_type=='Close':
            if self.fund_scheme_name=='financing':
                self.fin_daily_interest=track.loc[date,'cash']*(self.fin_nrdr-1.0)
                track.loc[date,'cash']=track.loc[date,'cash']*self.fin_nrdr
            else:    
                track.loc[date,'cash']=track.loc[date,'cash']*self.NRDR
        total=track.loc[date,'port_value']+track.loc[date,'cash']
        track.loc[date,'total_value']=total

    def _force_sell(self, date, cash_aim):
        track_rec=self.track.loc[date]
        cash_collected=0
        for tgt in self.port_tgts:
            value=track_rec[f'{tgt}_value']
            if value > cash_aim:
                self.action_dict[tgt]=-cash_aim
                break
            else:
                self.action_dict[tgt]=-value
                cash_collected+=value
            if cash_collected>=cash_aim:
                break
        self.trade(date,call_from='!FORCE_SELL!',price_type='Open')
 
    def _parse_ticker_perform(self):
        self.ticker_perform_dic={
            'header':['Tickers', 'Price', 'ShortLag', 'LongLag', 'Shares', 'Value',
                      'AccuInflow', 'AccuOutflow', 'CurrReturn']}
        tickers=self.port_tgts
        if self.forward_flag:
            date_now=self.dateseries[-2]
        else:
            date_now=self.dateseries[-1]
        op_df, real_acc=self.operation_df, self.real_acc
        for ticker in tickers:
            price_rec=self.port_hist[ticker].loc[date_now]
            #print(self.port_hist[ticker].loc[date_now])
            price=price_rec['Close']
            lastday_share=self.lastday_dic[f'{ticker}_share']
            lastday_value=self.lastday_dic[f'{ticker}_value']
            in_s, out_s=utils.cal_flow(op_df,ticker)
            #gain_s= float(lastday_value[0])-out_s-in_s
            gain_s= float(lastday_value[0][1:])-out_s-in_s
            in_r, out_r=utils.cal_flow(real_acc,ticker)
            #gain_r= float(lastday_value[1])-out_r-in_r
            gain_r= float(lastday_value[1][1:])-out_r-in_r
            if self.scheme_name == 'ma_cross':
                (ma_shortlag,shortvalue)=self.ma_cross[f'{ticker}_short']
                (ma_longlag,longvalue)=self.ma_cross[f'{ticker}_long']
                s2l=(shortvalue-longvalue)/longvalue
                s2l_txt=utils.fmt_value(s2l, pos_sign=True, vtype="pct")
                p2l=(price-longvalue)/longvalue
                p2l_txt=utils.fmt_value(p2l, pos_sign=True, vtype="pct")
                short_str=f'{utils.fmt_value(shortvalue, pos_sign=False)} (MA{ma_shortlag};{s2l_txt})'
                long_str=f'{utils.fmt_value(longvalue, pos_sign=False)} (MA{ma_longlag})'
                self.ticker_perform_dic[f'{ticker} (S)']=[
                    f'{utils.fmt_value(price, pos_sign=False)} ({p2l_txt})',short_str, long_str,
                    lastday_share[0], lastday_value[0], 
                    utils.fmt_value(in_s, pos_sign=False), utils.fmt_value(out_s, pos_sign=False),
                    utils.fmt_value(gain_s, pos_sign=False)]
                self.ticker_perform_dic[f'{ticker} (R)']=[
                    f'{utils.fmt_value(price, pos_sign=False)} ({p2l_txt})', short_str, long_str,
                    lastday_share[1], lastday_value[1], 
                    utils.fmt_value(in_r, pos_sign=False), utils.fmt_value(out_r, pos_sign=False),
                    utils.fmt_value(gain_r, pos_sign=False)]
            self.lastday_dic.pop(f'{ticker}_share')
            self.lastday_dic.pop(f'{ticker}_value')
    def trade_real(self,date):
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
                    f' cash:{track.loc[date,"cash"]:.2f}USD'+\
                    f' on {date.strftime("%Y-%m-%d")}')
    
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
        '''
        track['drawdown'].where(
            track['drawdown']>-track['fund_change'], other=-track['fund_change'],
            inplace=True)
        '''
        # baseline return
        if self.withbase:
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
        self.eval_dic=painter.append_dic_table(
            self.eval_dic, eval_table, 
            column_name=track_identity, index_name='Metrics')
        # last day track
        lstday_dic=track.iloc[-1].to_dict()
        lstday_dic['accum_return']=lstday_dic['accum_return']-1
         
        lstday_dic['drawdown']=-lstday_dic['drawdown'] 
        if self.withbase:
            lstday_dic['baseline_return']=lstday_dic['baseline_return']-1
            if lstday_dic['baseline_drawdown']>0:
                lstday_dic['baseline_drawdown']=-lstday_dic['baseline_drawdown'] 
            else:
                lstday_dic['baseline_drawdown']='N/A'
        lstday_dic=painter.fmt_dic(lstday_dic)
        self.lastday_dic=painter.append_dic_table(
            self.lastday_dic, lstday_dic,
            column_name=track_identity, index_name='Metrics')
        if self.cfg['POSTPROCESS'].getboolean('visualize'):
            
            self._form_att_dic()
            try:
                port_colors=self.cfg['POSTPROCESS']['port_colors'].split(',')
            except KeyError:
                port_colors=const.PORT_COLORS
            
            if self.forward_flag:
                if track_mark is None:
                    painter.draw_perform_fig(
                        track, self.port_tgts, fig_fn, port_colors, att_dic=self.att_dic)
                else:
                    painter.draw_perform_fig(
                        track, self.port_tgts, fig_fn, port_colors)
            else:
                if self.fund_scheme_name=='financing':
                    financing_flag=True
                else:
                    financing_flag=False
                painter.draw_perform_fig(
                    track[:-1].copy(), self.port_tgts, fig_fn, port_colors,
                    self.withbase, financing_flag, self.lev_flag, self.att_dic)
        try:
            if self.cfg['POSTPROCESS'].getboolean('dump_track'):
                if track_mark is None:
                    track.to_csv('track.csv')
                else:
                    track.to_csv('track_real.csv')
        except KeyError:
            pass
        #print(track.iloc[-1])
    def trade(self, date, call_from='DCA', price_type='NearOpen'):
        '''
        determine exact position change, for input
        action_dict= 
        {'SPY':5000,'SPXL':-1000}
        
        positive for buy, negative for sell 
        '''
        #self.risk_manage(date)
        track=self.track
        msg_prefix='[ON_TRADE]'
        trade_day=utils.find_trade_date(date, self.trading_dates)
        if trade_day != date:
            utils.write_log(f'{print_prefix}{msg_prefix} Trade day shift: {date} -> {trade_day}')
        #[('SPXL', -Val), ('SPY', Val)]
        cash_needed=sum(self.action_dict.values())
        cash_inhand=track.loc[date,'cash']
        adj_ratio=1.0
        if cash_needed>0 and cash_inhand<cash_needed:
            adj_ratio=cash_inhand/cash_needed
        act_tgt_lst = sorted(self.action_dict.items(), key=lambda x:x[1])
        for act_tgt in act_tgt_lst:
            tgt,val=act_tgt[0],act_tgt[1]*adj_ratio
            price_rec=self.port_hist[tgt].loc[trade_day]
            trade_price=utils.determ_price(price_rec, price_type)
            share, cash_fra=utils.cal_trade(trade_price, val)
            if not(share==0):
                track.loc[date,f'{tgt}_share']+=share
                track.loc[date,f'{tgt}_value']+=share*trade_price
                track.loc[date,'port_value']+=share*trade_price
                track.loc[date,'cash']-=share*trade_price
                self._feed_operation(date, tgt, share, trade_price)

                # write log
                log_data=f'{msg_prefix} -{call_from}- Trade signal captured:{share:.0f} shares'+\
                    f' of {tgt}@{trade_price:.2f}({share*trade_price:.2f}USD)'+\
                    f' cash left:{track.loc[date,"cash"]:.2f}USD'+\
                    f' on {date.strftime("%Y-%m-%d")}'
                
                # forward feed lastday msg
                if date==self.dateseries[-1] and self.forward_flag:
                    self.msg_dic=utils.feed_msg_title(
                        self.msg_dic, f'{tgt}:{share:.0f}@{trade_price:.2f}')
                    self.msg_dic=utils.feed_msg_body(
                        self.msg_dic, f'<h2>{log_data}</h2>')
                
                utils.write_log(print_prefix+log_data)

        track.loc[date,'total_value']= track.loc[date,'port_value']+track.loc[date,'cash']
        for tgt in self.port_tgts:
            self.action_dict[tgt]=0.0

    def _form_att_dic(self):
        track=self.track
        self.att_dic={
            'scheme_name':self.scheme_name,
            'init_total_asset':track.iloc[0]['total_value'],
            'total_nonlev_inflow':self.acc_act_fund,
            'total_nonlev_outflow':self.acc_out_fund,
            'norisk_scheme':self.norisk_scheme_name,
            'fund_scheme':self.fund_scheme_name,
        }
        if self.lev_flag:
            self.att_dic+={'init_net_asset':track.iloc[0]['net_value'],
            'init_lev_asset':track.iloc[0]['lev_value'],
            'total_lev_inflow':self.lev_acc_fund,
            'total_lev_paid_interest':self.lev_acc_paid}

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
       
        # operation records
        tb_msg=painter.table_print(
            self.operation_df.sort_values(by='Date',ascending=False).iloc[0:10],table_fmt='html')
        self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>Schemer Operations</h2>{tb_msg}')
        tb_msg=painter.table_print(
            self.real_acc.sort_values(by='Date',ascending=False).iloc[0:10],table_fmt='html')
        self.msg_dic=utils.feed_msg_body(self.msg_dic, f'<h2>Real Operations</h2>{tb_msg}')
        
        # form msg all
        title, content=utils.form_msg(self.msg_dic)
        io.archive_msg(self.cfg['SCHEMER']['out_msg_file'], title, content)
        
        
        if self.cfg['SCHEMER'].getboolean('send_msg'):
            messenger.gmail_send_message(self.cfg, title, content)
    
    def financing_msg_hdler(self):
        roll_date=self.dateseries[-1]
        self.msg_dic=utils.feed_msg_body(
            self.msg_dic, f'<h2>借款合约每日结算报告（截至{roll_date.strftime("%Y年%m月%d日")}）</h2>')
        meta_dic=self.meta_dic
        meta_dic=messenger.parse_financing_meta(self, meta_dic)
        self.msg_dic['title_lst'].append(meta_dic['借款合约编号'])
        tb_msg=painter.dic2html_CN(meta_dic)
        self.msg_dic=utils.feed_msg_body(self.msg_dic, tb_msg)
        if self.fin_sup_contract !='': 
            self.msg_dic=utils.feed_msg_body(
                self.msg_dic, f'<h3>合约补充条款（截至{roll_date.strftime("%Y年%m月%d日")}）</h3>')        
            self.msg_dic=utils.feed_msg_body(self.msg_dic, self.fin_sup_contract)
        # form msg all
        title, content=utils.form_msg(self.msg_dic)
        io.archive_msg(self.cfg['SCHEMER']['out_msg_file'], title, content)
        
        
        if self.cfg['SCHEMER'].getboolean('send_msg'):
            messenger.gmail_send_message(self.cfg, title, content)
    

            
# ---Unit test---
if __name__ == '__main__':
    pass
