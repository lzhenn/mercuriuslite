import mercuriuslite
mercuriuslite.copy_cfg('config.case.ini')

agent=mercuriuslite.Mercurius()
#agent.as_spider()
agent.as_predictor()
agent.predictor.train()
agent.predictor.predict()
agent.as_evaluator(agent.predictor)
agent.evaluator.bayes_test()
agent.predictor.fast_plot()
