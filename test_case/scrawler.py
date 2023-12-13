import mercuriuslite

agent=mercuriuslite.Mercurius(cfgfn='config.scrawler.ini')
agent.as_crawler()
#agent.crawler.fetch(type='div')
agent.crawler.fetch(inperiod='max')
agent.crawler.persist()
