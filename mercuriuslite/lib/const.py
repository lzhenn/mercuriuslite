
def init(cfg):
    
    # changable by config
    global CASH_IN_HAND, LEVERAGE_INTEREST, NO_RISK_RETURN, MAJOR_DRAWDOWN
    
    NO_RISK_RETURN=float(cfg['CONST']['NO_RISK_RETURN'])
    try: 
        LEVERAGE_INTEREST=float(cfg['CONST']['LEVERAGE_INTEREST']) 
    except KeyError:
        pass
    CASH_IN_HAND=float(cfg['CONST']['CASH_IN_HAND'])
    MAJOR_DRAWDOWN=float(cfg['CONST']['MAJOR_DRAWDOWN']) 


PORT_COLORS=['blue', 'red', 'purple', 'darkcyan', 'gold', 'grey', 'pink']
LEV_TICKERS={'SPXL':3.0, 'TMF':3.0, 'TQQQ':3.0}
# Trading
TRAD_DAYS={
    'day':1, 'week':5, 'mon':21, 'qtr':63, 'yr':252
}
DAYS_PER_YEAR=365
DAYS_PER_MONTH=30

HOLIDAYS=['20230904','20231123','20231225',
          '20240101','20240115','20240219','20240329','20240527','20240619',
          '20240704','20240902','20241128','20241225',
          '20250101','20250120','20250217','20250418','20250526','20250619',
          '20250704','20250901','20251127','20251225',
          '20260101','20260119','20260216','20260403','20260525','20260619',
          '20260703','20260907','20261126','20261225']

# log
HLINE='------------------'

# Figures
TINY_SIZE = 6
SM_SIZE = 8
MID_SIZE = 12
LARGE_SIZE = 14
DPI=180
