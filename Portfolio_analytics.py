from pandas import read_csv, to_datetime, DataFrame
import pyfolio as pf
from API_test import get_portfolio_history
from datetime import datetime
from numpy import nan

PT_id = 'SectorRFRank_10082022'
since = '2022-10-15'

YmdHMS_format = "%Y-%m-%d-%H-%M-%S"
Ymd_format = "%Y-%m-%d"
S_format = "%f"


df_pv = read_csv(f'Results/{PT_id}/portfolio_values.csv')
df_pv['Datetime'] = to_datetime(df_pv['Datetime'], format=YmdHMS_format)
df_pv['Datetime'] = df_pv['Datetime'].apply(lambda x: x.strftime(Ymd_format))
df_pv['Datetime'] = to_datetime(df_pv['Datetime'])
df_pv = df_pv.drop_duplicates(subset='Datetime', keep='last').sort_values(by='Datetime').set_index('Datetime')
df_pv = df_pv.loc[since:, :]

df_bm = read_csv('/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/daily/SPY.csv')
df_bm['Date'] = to_datetime(df_bm['Date'])
df_bm.set_index('Date', inplace=True)
df_bm = df_bm.loc[since:, :]
df_bm['SPY'] = df_bm['Adj Close'].pct_change()


pf.create_full_tear_sheet(
    df_pv['equity'].pct_change(), 
    benchmark_rets=df_bm['SPY'],
    test_path=f'/Users/yueyuchen/Documents/Academy/Research/PaperTrading/Results/{PT_id}'
)