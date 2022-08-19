from multiprocessing.util import is_exiting
import os
from pandas import read_csv, to_datetime, DataFrame
from signals import signal_map
from alpaca_api import alpaca_api
from datetime import datetime


class paper_trading():

    def __init__(self, id: str, signal_params: dict, init_value: float) -> None:
        self.id = id
        self.result_path = f'./Results/{self.id}'
        self.signal_params = signal_params
        self.api = alpaca_api()
        self.init_value = init_value
        self.now = datetime.now()

    def is_existing_pt(self):

        return os.path.exists(self.result_path)

    def make_result_dir(self):

        os.mkdir(self.result_path)

    def reset_portfolio(self):

        self.api.close_all_positions()

    def load_entries(self):

        self.df_orders = read_csv(f'{self.result_path}/orders.csv')
        self.df_positions = read_csv(f'{self.result_path}/positions.csv')
        self.df_saved_signal_data = read_csv(
            f'{self.result_path}/signal_data.csv')

    def save_entries(self):

        self.df_orders.to_csv(f'{self.result_path}/orders.csv')
        self.df_positions.to_csv(f'{self.result_path}/positions.csv')
        self.df_signal_data.to_csv(
            f'{self.result_path}/signal_data.csv')

    def load_signal(self):

        signal_name = self.signal_params['name']
        signal_params = self.signal_params['params']
        signal_data_path = self.signal_params['data_path']
        signal_ticker = self.signal_params['ticker']

        self.signal = signal_map[signal_name](
            signal_name, signal_data_path, signal_ticker, signal_params)

        self.df_signal_data = self.signal.compute_signal()

        self.last_trigger = self.signal.get_last_trigger()

        self.last_signal_data_dt = self.signal.get_last_data_dt()

    def sizer(self, pct):

        close = self.df_signal_data['Close'].iloc[-1]

        qty = self.init_value*pct//close

        side = 'buy' if self.last_trigger[-1] == 1 else 'sell'

        order_params = {
            "symbol": self.signal_params['ticker'],
            "qty": qty,
            "type": 'market',
            "side": side,
            "time_in_force": 'day'
        }

        return order_params

    def record_existing_open_orders_and_new_orders(self):

        if not self.df_orders.empty:

            open_orders = []

            for id in self.df_orders[self.df_orders['status'].isin(self.api.unfinished_order_status), 'id'].values:

                open_orders.append(self.api.get_order(id=id))

        if self.last_signal_data_dt == self.last_trigger[0]:

            order_params = self.sizer(0.5)

            open_orders.append(self.api.create_order(order_params))

        df_open_orders = DataFrame(open_orders)
        df_open_orders['Datetime'] = self.now

        self.df_orders = self.df_orders.append(
            df_open_orders.set_index('Datatime'))

    def record_new_orders(self):

        order_params = self.sizer(0.5)

        orders = self.api.create_order(order_params)

        orders['Datetime'] = self.now

        self.df_orders = DataFrame(orders).set_index('Datatime')

    def update_positions(self):

        positions = self.api.get_all_positions()

        positions['Datetime'] = self.now

        self.df_positions = self.df_positions.append(
            DataFrame(positions).set_index('Datatime'))

    def update_entries(self):

        self.load_signal()

        if self.is_existing_pt():

            self.load_entries()

            self.update_positions()

            self.record_existing_open_orders_and_new_orders()

            self.save_entries()

        else:

            self.make_result_dir()

            self.record_new_orders()

            self.df_positions = DataFrame()

            self.save_entries()
