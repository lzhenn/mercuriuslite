import concurrent.futures
import mercuriuslite
import itertools

def run_strategy(c):
    sp_dic = {'S_ma_cross': ['paras', f'PClose,{c[0]},{c[1]}']}
    agent = mercuriuslite.Mercurius(cfgfn='config.schemer.ini', cfg_spdic=sp_dic)
    agent.as_trader()
    agent.trader.account_evolve()
    df = agent.trader.track
    twr = df.iloc[-1]['accum_return']
    mdd = -df['drawdown'].max()
    mdd_day=df['drawdown'].idxmax()
    trade_times = len(agent.trader.operation_df)
    total_days = (df.index[-1] - df.index[0]).days
    print(f'ma_short:{c[0]},ma_long:{c[1]},NAV:{twr:.4f},MaxDD:{mdd:.4f}@{mdd_day.strftime("%Y-%m-%d")},Trades:{total_days/trade_times:.1f}days/time')

def main():
    
    #short_ma = [5, 10, 15, 20, 25, 30]
    short_ma = [4, 5, 6, 7,8]
    #long_ma = [10,12,15,18,20,22,25,27,30,35,40,45,50]
    #short_ma = [3,4,5,6,7,9,12]
    
    long_ma = [50, 70, 100, 120, 150, 200, 220, 280, 300, 400, 500, 600, 800]
    long_ma = [80,90,95,100,105,110]
    #long_ma = [150, 175, 200, 210, 220, 250]
    #long_ma = [15,20,30,50, 60, 70, 80, 90, 100, 120, 150, 180, 200, 210, 220, 250, 300]
    combines = list(itertools.product(short_ma, long_ma))
    with concurrent.futures.ProcessPoolExecutor(max_workers=6) as executor:
        for c in combines:
            executor.submit(run_strategy, c)

if __name__ == '__main__':
    main()