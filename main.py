from paper_trading import paper_trading
from datetime import datetime

time = datetime.now()

YEAR = 252
PT_id = 'SectorRFRank_10082022'  # time.strftime("%Y_%m_%d_%H_%M_%S")

signal_params = {
    'name': 'SectorRankSignal',
    'params': {'num_long': 3, 'num_short': 3, 'lookahead': 10, 'load_data_history_length': 3*YEAR},
    'ticker': ['XLK', 'XLP', 'XLB', 'XLF', 'XLV', 'XLY', 'XLE', 'XLU', 'XLI'],
    'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/daily',
}

execution_params = {
    'rank_pct': {0: 0.2, 1: 0.15, 2: 0.15, 6: 0.15, 7: 0.15, 8: 0.15},
    'trade_smallest_qty': 10
}

initial_value = 100000
PT = paper_trading(PT_id, signal_params, execution_params, initial_value)
PT.update_entries()

# Momentum signal
# signal_params = {
#     'name' : 'MomentumCrossoverSignal',
#     'params': {'short_period': 5, 'long_period': 25},
#     'ticker': 'SPY',
#     'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/intraday'
# }

# execution_params = {
#     'single_pos_pct': {'SPY': 0.5},
#     'trade_smallest_qty': 10
# }