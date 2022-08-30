from multiprocessing.util import is_exiting
import os
from pandas import read_csv, to_datetime, DataFrame
from signals import signal_map
from alpaca_api import alpaca_api
from datetime import datetime
import time

YmdHMS_format = "%Y-%m-%d-%H-%M-%S"


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

        self.df_orders = read_csv(
            f'{self.result_path}/orders.csv')
        self.last_order_status_dt = datetime(year=1900, month=1, day=1)
        if not self.df_orders.empty:
            self.df_orders['Datetime'] = to_datetime(
                self.df_orders['Datetime'], format=YmdHMS_format)
            self.df_orders.set_index('Datetime', inplace=True)
            self.last_order_status_dt = self.df_orders.index[-1]

        self.df_positions = read_csv(
            f'{self.result_path}/positions.csv')
        if not self.df_positions.empty:
            self.df_positions['Datetime'] = to_datetime(
                self.df_positions['Datetime'], format=YmdHMS_format)
            self.df_positions.set_index('Datetime', inplace=True)

        self.df_saved_signal_data = read_csv(
            f'{self.result_path}/signal_data.csv', index_col=['Datetime'])

    def save_entries(self):
        self.df_orders.index = self.df_orders.index.strftime(YmdHMS_format)
        self.df_orders.to_csv(f'{self.result_path}/orders.csv')

        self.df_positions.index = self.df_positions.index.strftime(
            YmdHMS_format)
        self.df_positions.to_csv(f'{self.result_path}/positions.csv')
        self.df_signal_data.to_csv(
            f'{self.result_path}/signal_data.csv')

    def load_signal(self):

        signal_name = self.signal_params['name']
        signal_params = self.signal_params['params']
        signal_data_path = self.signal_params['data_path']
        signal_ticker = self.signal_params['ticker']

        self.signal = signal_map[signal_name](
            signal_name, signal_data_path, signal_ticker, **signal_params)

        self.df_signal_data = self.signal.compute_signal()

        self.last_trigger = self.signal.get_last_trigger()

        self.last_signal_data_dt = self.signal.get_last_data_dt()

    def get_qty_available(self, ticker):

        return int(self.df_positions.loc[self.df_positions['symbol'] == ticker, 'qty_available'].iloc[-1])

    def sizer(self, pct):

        close = self.df_signal_data['Close'].iloc[-1]

        target_qty = self.init_value*pct//close

        side = 'buy' if self.last_trigger[-1] == 1 else 'sell'

        avail_qty = self.get_qty_available(self.signal_params['ticker'])

        if (side == 'buy' and avail_qty < 0) or (side == 'sell' and avail_qty > 0):
            close_first = True
            qty = target_qty
        elif side == 'buy' and avail_qty >= 0:
            qty = target_qty - avail_qty
            qty, side = -qty, 'sell' if qty < 0 else qty, side
            close_first = False
        elif side == 'sell' and avail_qty <= 0:
            qty = target_qty + avail_qty
            qty, side = -qty, 'buy' if qty < 0 else qty, side
            close_first = False

        order_params = {
            "symbol": self.signal_params['ticker'],
            "qty": qty,
            "type": 'market',
            "side": side,
            "time_in_force": 'day'
        }

        close_order_side = 'buy' if avail_qty < 0 else 'sell'

        close_order_params = {
            "symbol": self.signal_params['ticker'],
            "qty": abs(avail_qty),
            "type": 'market',
            "side": close_order_side,
            "time_in_force": 'day'
        }

        return order_params, close_first, close_order_params

    def record_existing_open_orders_and_new_orders(self):

        open_orders = []

        if not self.df_orders.empty:

            df_temp = self.df_orders.reset_index()

            for id in df_temp.loc[(df_temp['status'].isin(self.api.unfinished_order_status)) & (df_temp['Datetime'] == self.last_order_status_dt), 'id'].values:

                open_orders.append(self.api.get_order(id=id))

        if self.last_order_status_dt < self.last_trigger[0]:

            order_params, close_first, close_order_params = self.sizer(0.5)

            if close_first:
                open_orders.append(self.api.create_order(**close_order_params))
                time.sleep(1)

            open_orders.append(self.api.create_order(**order_params))

        df_open_orders = DataFrame(open_orders)
        df_open_orders['Datetime'] = self.now

        self.df_orders = self.df_orders.append(
            df_open_orders.set_index('Datetime'))

    def record_new_orders(self):

        order_params = self.sizer(0.5)

        orders = self.api.create_order(**order_params)

        self.df_orders = DataFrame(
            orders, index=[self.now.strftime(YmdHMS_format)])

        self.df_orders.index.name = 'Datetime'

    def update_positions(self):

        positions = self.api.get_all_positions()

        self.df_positions = self.df_positions.append(
            DataFrame(positions, index=[self.now]))

        self.df_positions.index.name = 'Datetime'

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
