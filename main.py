from paper_trading import paper_trading
from datetime import datetime

time = datetime.now()

PT_id = 'Momentum_08242022'#time.strftime("%Y_%m_%d_%H_%M_%S")

signal_params = {
    'name' : 'MomentumCrossoverSignal',
    'params': {'short_period': 5, 'long_period': 25},
    'ticker': 'SPY',
    'data_path': '/Users/yueyuchen/Documents/Academy/Research/MarketWatch/data/intraday'
}

execution_params = {
    'single_pos_pct': {'SPY': 0.5},
    'trade_smallest_qty': 10
}

initial_value = 100000
PT = paper_trading(PT_id, signal_params, execution_params, initial_value)
PT.update_entries()