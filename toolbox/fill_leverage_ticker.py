import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
date_parser = lambda date: datetime.datetime.strptime(
    date.split()[0],'%Y-%m-%d')
arch_path='/Users/zhenningli/work/mercuriuslite/data/archive/'

X_ticker='SPY'
Y_ticker='SPLG'

# Read in the Y and X data
Y_data = pd.read_csv(f'{arch_path}/{Y_ticker}.csv',date_parser=date_parser, index_col='Date')
X_data = pd.read_csv(f'{arch_path}/{X_ticker}.csv',date_parser=date_parser, index_col='Date')
# Drop any rows that have NaN values
X_data['Cx']=X_data['Close'].diff(periods=-1)/X_data['Close']
Y_data['Cy']=Y_data['Close'].diff(periods=-1)/Y_data['Close']

# Merge the two dataframes on the 'Date' column
merged_data = pd.merge(X_data, Y_data, on='Date',how='outer' )
merged_data = merged_data.dropna()

# Build model
close_model=LinearRegression().fit(merged_data[['Cx']].values, merged_data[['Cy']].values)
Hx=merged_data[['High_x']].values/merged_data[['Close_x']].values
Hy=merged_data[['High_y']].values/merged_data[['Close_y']].values
high_model=LinearRegression().fit(Hx, Hy)
Lx=merged_data[['Low_x']].values/merged_data[['Close_x']].values
Ly=merged_data[['Low_y']].values/merged_data[['Close_y']].values
low_model=LinearRegression().fit(Lx, Ly)
Ox=merged_data[['Open_x']].values/merged_data[['Close_x']].values
Oy=merged_data[['Open_y']].values/merged_data[['Close_y']].values
open_model=LinearRegression().fit(Ox, Oy)

print(f'Close Model Score: {close_model.score(merged_data[["Cx"]].values, merged_data[["Cy"]].values)}')
print(f'High Model Score: {high_model.score(Hx, Hy)}')
print(f'Low Model Score: {low_model.score(Lx, Ly)}')
print(f'Open Model Score: {open_model.score(Ox, Oy)}')
for index, row in X_data.iterrows():
    if index not in Y_data.index:
        if not(np.isnan(row['Cx'])):
            Y_data.loc[index, 'Cy'] = close_model.predict([[row['Cx']]])[0][0]

Y_data=Y_data.sort_index()
idY=Y_data.index
for index, row in Y_data[::-1].iterrows():
    if np.isnan(row['Close']):
        id=idY.get_loc(index)
        Y_data.loc[index, 'Close'] = Y_data.loc[idY[id+1], 'Close'] /(1.0- Y_data.loc[index, 'Cy'])
        Hx=X_data.loc[index, 'High']/X_data.loc[index, 'Close']
        Y_data.loc[index, 'High'] = high_model.predict([[Hx]])[0][0]*Y_data.loc[index, 'Close']
        Lx=X_data.loc[index, 'Low']/X_data.loc[index, 'Close']
        Y_data.loc[index, 'Low'] = low_model.predict([[Lx]])[0][0]*Y_data.loc[index, 'Close']
        Ox=X_data.loc[index, 'Open']/X_data.loc[index, 'Close']
        Y_data.loc[index, 'Open'] = open_model.predict([[Ox]])[0][0]*Y_data.loc[index, 'Close'] 
Y_data=Y_data.drop(columns=['Cy']) 
print(Y_data)

# Write the updated Y dataframe to a new CSV file
Y_data.to_csv(f'{arch_path}/{Y_ticker}_updated.csv')
