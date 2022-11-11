from datetime import datetime
import os
from pandas import read_csv, to_datetime, DataFrame
from signals import signal_map

time = datetime.now()

YEAR = 252

signal_params = {
    'name': 'SectorRankSignal',
    'params': {'num_long': 3, 'num_short': 3, 'lookahead': 10, 'load_data_history_length': 22*YEAR},
    'ticker': ['XLK', 'XLP', 'XLB', 'XLF', 'XLV', 'XLY', 'XLE', 'XLU', 'XLI'],
    'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/daily',
}

execution_params = {
    'rank_pct': {0: 0.2, 1: 0.15, 2: 0.15, 6: 0.15, 7: 0.15, 8: 0.15},
    'trade_smallest_qty': 10
}

signal_name = signal_params['name']
signal_args = signal_params['params']
signal_data_path = signal_params['data_path']
signal_ticker = signal_params['ticker']

signal = signal_map[signal_name](
    signal_name, signal_data_path, signal_ticker, **signal_args)

df_signal_data = signal.compute_signal()

predictions = signal.get_predictions()

print(df_signal_data)