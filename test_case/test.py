import mercuriuslite
#mercuriuslite.copy_cfg('config.ma_cross.ini')

agent=mercuriuslite.Mercurius(cfgfn='config.ma_cross.ini')

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
agent.trader.account_evolve()