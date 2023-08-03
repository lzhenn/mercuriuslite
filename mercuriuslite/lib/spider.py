#!/usr/bin/env python3
"""specific module for IO"""
# ---imports---
import yfinance as yf
import os
# ---Module regime consts and variables---
print_prefix='lib.spider>>'


# ---Classes and Functions---
def fetch(ticker, archive_dir):
    """ Fetch data from yahoo finance """

    ticker_hdl=yf.Ticker(ticker)
    hist=ticker_hdl.history(period='max')
    fn=os.path.join(archive_dir,ticker)+'.csv'
    hist.to_csv(fn)
# ---Unit test---
if __name__ == '__main__':
    pass