#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
import yfinance as yf
import os, shutil
from . import utils, io
# ---Module regime consts and variables---
print_prefix='lib.crawler>>'

class Andariel:
    def __init__(self, mercurius):
        self.cfg=mercurius.cfg
        self.tickers=self.cfg['SCRAWLER']['tickers'].replace(' ','').split(',')
        self.archive_dir=self.cfg['SCRAWLER']['archive_dir']
        self.ltm_dir=mercurius.ltm_dir
    # ---Classes and Functions---
    def fetch(self, inperiod='1mo'):
        """ Fetch data from yahoo finance """
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
        for ticker in self.tickers:
            utils.write_log(f'{print_prefix}Fetching {ticker}...')
            ticker_hdl=yf.Ticker(ticker)
            hist=ticker_hdl.history(period=inperiod)
            fn=os.path.join(self.archive_dir,ticker)+'.csv'
            hist.to_csv(fn)
            
    def persist(self):
        """ Persist data to long-term storage directory """
        
        if not os.path.exists(self.ltm_dir):
            os.makedirs(self.ltm_dir)
        
        for ticker in self.tickers:

            realtime_fn=os.path.join(self.archive_dir,ticker+'.csv')
            ltm_fn=os.path.join(self.ltm_dir,ticker+'.csv')
                
            if not os.path.exists(ltm_fn):
                utils.write_log(f'{print_prefix}Persisting non-existent data for {ticker}...')
                shutil.copyfile(realtime_fn, ltm_fn)
            else:
                
                realtime_df = io.load_hist(self.archive_dir, ticker)
                longterm_df = io.load_hist(self.ltm_dir, ticker)

                # Find the latest date in the longterm data
                latest_date = longterm_df.index.max()
                # Filter the realtime data for newer records
                newer_realtime_df = realtime_df[realtime_df.index > latest_date]
                if newer_realtime_df.empty:
                    utils.write_log(
                        f'{print_prefix}No new data for {ticker}, latest date is {latest_date}...')
                    continue
                
                strt_date,end_date=newer_realtime_df.index[0],newer_realtime_df.index[-1]
                
                utils.write_log(
                    f'{print_prefix}Persisting existing data from {strt_date} to {end_date} for {ticker}...')
                
                # Append the newer records to the longterm data
                longterm_df = longterm_df.append(newer_realtime_df)

                # Save the updated longterm data to file
                longterm_df.to_csv(ltm_fn)

# ---Unit test---
if __name__ == '__main__':
    pass