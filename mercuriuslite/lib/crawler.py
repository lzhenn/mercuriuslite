#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
import yfinance as yf
import os
# ---Module regime consts and variables---
print_prefix='lib.crawler>>'

class Andariel:
    def __init__(self,cfg):
        self.cfg=cfg
        self.tickers=self.cfg['SCRAWLER']['tickers'].replace(' ','').split(',')
        self.archive_dir=self.cfg['SCRAWLER']['archive_dir']
        self.ltm_dir=self.cfg['SCRAWLER']['ltm_dir']
    # ---Classes and Functions---
    def fetch(self, inperiod='1mo'):
        """ Fetch data from yahoo finance """
        for ticker in self.tickers:
            ticker_hdl=yf.Ticker(ticker)
            hist=ticker_hdl.history(period=inperiod)
            fn=os.path.join(archive_dir,ticker)+'.csv'
            hist.to_csv(fn)
            
    def persist(ticker, ltm_dir):
        """ Persist data to long-term storage directory """
        if not os.path.exists(ltm_dir):
            os.makedirs(ltm_dir)
        if not os.path.exists(os.path.join(ltm_dir, ticker+'.csv')):
            fetch(ticker, ltm_dir)
        
# ---Unit test---
if __name__ == '__main__':
    pass