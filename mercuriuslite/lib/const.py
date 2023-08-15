
def init(cfg):
    # changable by config
    global CASH_IN_HAND, NO_RISK_RETURN, MAJOR_DRAWDOWN
    NO_RISK_RETURN=float(cfg['CONST']['NO_RISK_RETURN']) 
    CASH_IN_HAND=float(cfg['CONST']['CASH_IN_HAND'])
    MAJOR_DRAWDOWN=float(cfg['CONST']['MAJOR_DRAWDOWN']) 



# Trading
TRAD_DAYS={
    'day':1, 'week':5, 'mon':21, 'qtr':63, 'yr':252
}
DAYS_PER_YEAR=365
DAYS_PER_MONTH=30
# log
HLINE='------------------'

# Figures
SM_SIZE = 8
MID_SIZE = 12
LARGE_SIZE = 14
DPI=240
