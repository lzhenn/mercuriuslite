import mercuriuslite
agent=mercuriuslite.Mercurius(cfgfn='config.schemer.ini')
agent.as_trader()
agent.trader.account_evolve()