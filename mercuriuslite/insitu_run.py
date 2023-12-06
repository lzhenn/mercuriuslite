#!/usr/bin/env python3
'''
Date: Jul 30, 2023
mercuriuslite is 

This is the main script to drive the model

History:
Jul 30, 2023 --- Kick off the project 

L_Zealot
'''

from . import __main__ as mercuriuslite

# in-situ runs
if __name__ == '__main__':
    agent=mercuriuslite.Mercurius(cfgfn='mercuriuslite/conf/config.case.ini')
    agent.as_predictor()
    agent.predictor.train()
    agent.predictor.predict()