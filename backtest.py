from datetime import datetime
import os
from pandas import read_csv, to_datetime, DataFrame, MultiIndex
from signals import signal_map
import matplotlib  
matplotlib.use('TkAgg') 
import pyfolio as pf

time = datetime.now()

YEAR = 252
YmdHMS_format = "%Y-%m-%d-%H-%M-%S"
Ymd_format = "%Y-%m-%d"
history_length = 22*YEAR

signal_params = {
    'name': 'SectorRankSignal',
    'params': {'num_long': 3, 'num_short': 3, 'lookahead': 10, 'load_data_history_length': history_length},
    'ticker': ['XLK', 'XLP', 'XLB', 'XLF', 'XLV', 'XLY', 'XLE', 'XLU', 'XLI'],
    'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/daily',
}

Benchmark_params = {
    'name': 'BuyNHold',
    'params': {'load_data_history_length': history_length},
    'ticker': 'SPY',
    'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/daily',
}

execution_params = {
    'rank_pct': {0: 0.2, 1: 0.15, 2: 0.15, 6: -0.15, 7: -0.15, 8: -0.15},#,{0: -0.15, 1: -0.15, 2: -0.15, 6: 0.15, 7: 0.15, 8: 0.15}
    'trade_smallest_qty': 10
}

signal = signal_map[signal_params['name']](
    signal_params['name'], signal_params['data_path'], signal_params['ticker'], **signal_params['params'])

BM = signal_map[Benchmark_params['name']](
    Benchmark_params['name'], Benchmark_params['data_path'], Benchmark_params['ticker'], **Benchmark_params['params'])

df_bm = BM.get_data()
df_bm = df_bm.rename(columns={'Adj Close': BM.ticker})

df_backtest = signal.compute_backtest()
df_backtest['weight'] = df_backtest['Rank'].replace(execution_params['rank_pct'])
df_backtest.loc[~df_backtest['Rank'].isin(execution_params['rank_pct']), 'weight'] = 0.
df_backtest = df_backtest.unstack('ticker')

ret_cols = MultiIndex.from_product([['Ret'], df_backtest['Adj Close'].columns])
df_backtest[ret_cols] = df_backtest['Adj Close'].pct_change()
df_backtest['Tot_ret'] = (df_backtest['Ret'] * df_backtest['weight']).sum(axis=1)
df_backtest['Correct'] = (df_backtest['Ret'] * df_backtest['weight'] > 0.).sum(axis=1)
df_backtest['PV'] = df_backtest['Tot_ret'].add(1).cumprod()
df_analyse = df_backtest['PV'].to_frame().merge(df_bm[BM.ticker].loc[df_backtest.index].to_frame(), left_index=True, right_index=True)
df_analyse = df_analyse.div(df_analyse.iloc[0,:])

test_path = f'/Users/yueyuchen/Documents/Academy/Research/PaperTrading/backtest_analysis/{signal_params["name"]}/{time.strftime(Ymd_format)}'
if not os.path.exists(test_path):
    os.makedirs(test_path)
pf.create_full_tear_sheet(
    df_analyse['PV'].pct_change(), 
    benchmark_rets=df_analyse[BM.ticker].pct_change(),
    test_path=test_path
)
print(df_backtest['Correct'].describe())