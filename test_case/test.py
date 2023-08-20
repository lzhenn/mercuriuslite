import mercuriuslite
mercuriuslite.copy_cfg('config.case.ini')

agent=mercuriuslite.Mercurius()

#agent.as_crawler()
#agent.crawler.fetch()
#agent.crawler.fetch(inperiod='max')
#agent.crawler.persist()

#agent.as_predictor()
#agent.predictor.train()
#agent.predictor.predict()

#agent.as_evaluator(agent.predictor)
#agent.evaluator.bayes_test()
#agent.predictor.fast_plot()

#agent.as_referee()
#agent.referee.judge()

agent.as_trader()
#agent.trader.realtime_trade()
agent.trader.backtest()