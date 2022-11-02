from multiprocessing.util import is_exiting
import os
from pandas import read_csv, to_datetime, DataFrame
from signals import signal_map
from alpaca_api import alpaca_api
from datetime import datetime
import time

YmdHMS_format = "%Y-%m-%d-%H-%M-%S"
Ymd_format = "%Y-%m-%d"


class paper_trading():

    def __init__(self, id: str, signal_params: dict, execution_params: dict, init_value: float) -> None:
        self.id = id
        self.result_path = f'./Results/{self.id}'
        self.signal_params = signal_params
        self.api = alpaca_api()
        self.init_value = init_value
        self.now = datetime.now()
        self.execution_params = execution_params

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
        else:
            self.df_orders = DataFrame()

        self.df_positions = read_csv(
            f'{self.result_path}/positions.csv')
        if not self.df_positions.empty:
            self.df_positions['Datetime'] = to_datetime(
                self.df_positions['Datetime'], format=YmdHMS_format)
            self.df_positions.set_index('Datetime', inplace=True)
            self.last_positions_dt = self.df_positions.index[-1]
        else:
            self.df_positions = DataFrame()

        self.df_pv = read_csv(
            f'{self.result_path}/portfolio_values.csv')
        if not self.df_pv.empty:
            self.df_pv['Datetime'] = to_datetime(
                self.df_pv['Datetime'], format=YmdHMS_format)
            self.df_pv.set_index('Datetime', inplace=True)
        else:
            self.df_pv = DataFrame()

        self.df_saved_predictions = read_csv(
            f'{self.result_path}/predictions.csv')
        if not self.df_saved_predictions.empty:
            self.df_saved_predictions['date'] = to_datetime(
                self.df_saved_predictions['date'], format=Ymd_format)
            self.df_saved_predictions.set_index(['ticker','date'], inplace=True)
        else:
            self.df_saved_predictions = DataFrame()
            

    def save_entries(self):
        self.df_orders.index = self.df_orders.index.strftime(YmdHMS_format)
        self.df_orders.to_csv(f'{self.result_path}/orders.csv')

        if not self.df_positions.empty:
            self.df_positions.index = self.df_positions.index.strftime(
                YmdHMS_format)
        self.df_positions.to_csv(f'{self.result_path}/positions.csv')

        if not self.df_pv.empty:
            self.df_pv.index = self.df_pv.index.strftime(
                YmdHMS_format)
        self.df_pv.to_csv(f'{self.result_path}/portfolio_values.csv')

        self.df_signal_data.to_csv(
            f'{self.result_path}/signal_data.csv')
            
        self.df_saved_predictions = self.df_saved_predictions.append(self.predictions).drop_duplicates()
        self.df_saved_predictions.to_csv(
            f'{self.result_path}/predictions.csv')

    def load_signal(self):

        signal_name = self.signal_params['name']
        signal_params = self.signal_params['params']
        signal_data_path = self.signal_params['data_path']
        signal_ticker = self.signal_params['ticker']

        self.signal = signal_map[signal_name](
            signal_name, signal_data_path, signal_ticker, **signal_params)

        self.df_signal_data = self.signal.compute_signal()

        self.predictions = self.signal.get_predictions()


        # self.last_trigger = self.signal.get_last_trigger()

        # self.last_signal_data_dt = self.signal.get_last_data_dt()

    def get_qty_available(self, ticker):

        if not hasattr(self, 'df_positions') or self.df_positions.empty:
            return 0
        df_temp = self.df_positions.reset_index()

        df_temp = df_temp.loc[(df_temp['Datetime'] == self.last_positions_dt) & (
            df_temp['symbol'] == ticker), :]
        if df_temp.empty:
            return 0
        else:
            return int(df_temp['qty_available'].iloc[0])

    def sizer(self, tick, pct, close, side):

        target_qty = self.init_value*pct//close

        avail_qty = self.get_qty_available(tick)

        if (side == 'buy' and avail_qty < 0) or (side == 'sell' and avail_qty > 0):
            close_first = True
            qty = target_qty
        elif side == 'buy' and avail_qty >= 0:
            qty = target_qty - avail_qty
            qty, side = (-qty, 'sell') if qty < 0 else (qty, side)
            close_first = False
        elif side == 'sell' and avail_qty <= 0:
            qty = target_qty + avail_qty
            qty, side = (-qty, 'buy') if qty < 0 else (qty, side)
            close_first = False
        elif side=='Neu':
            qty = 0
            side = 'buy' if avail_qty<=0 else 'sell'
            close_first = True if abs(avail_qty)>0 else False


        order_params = {
            "symbol": tick,
            "qty": qty,
            "type": 'market',
            "side": side,
            "time_in_force": 'day'
        }

        close_order_side = 'buy' if avail_qty < 0 else 'sell'

        close_order_params = {
            "symbol": tick,
            "qty": abs(avail_qty),
            "type": 'market',
            "side": close_order_side,
            "time_in_force": 'day'
        }

        return order_params, close_first, close_order_params

    def record_existing_open_orders_and_new_orders(self):

        self.open_orders = []

        if not self.df_orders.empty:

            df_temp = self.df_orders.reset_index()

            for id in df_temp.loc[(df_temp['status'].isin(self.api.unfinished_order_status)) & (df_temp['Datetime'] == self.last_order_status_dt), 'id'].values:

                self.open_orders.append(self.api.get_order(id=id))

        # if self.last_order_status_dt < self.last_trigger[0]:

        self.record_new_orders(init_list=False)

    def record_new_orders(self, init_list=True):

        if init_list:
            self.open_orders = []

        unfinished_order_symbols = [od['symbol'] for od in self.open_orders]

        for idx, row in self.predictions.iterrows():

            if idx[0] in unfinished_order_symbols:
                continue

            order_params, close_first, close_order_params = self.sizer(
                idx[0], self.execution_params['rank_pct'].get(int(row.Rank), 0.),
                row.Close, row.side
            )

            if close_first:
                self.open_orders.append(
                    self.api.create_order(**close_order_params))
                time.sleep(1)
            if order_params['qty'] > self.execution_params['trade_smallest_qty']:
                
                self.open_orders.append(self.api.create_order(**order_params))

        df_open_orders = DataFrame(self.open_orders)
        df_open_orders['Datetime'] = self.now

        self.df_orders = self.df_orders.append(
            df_open_orders.set_index('Datetime'))

    def update_positions(self):

        positions = self.api.get_all_positions()

        self.df_positions = self.df_positions.append(
            DataFrame(positions, index=[self.now]*len(positions)))

        self.df_positions.index.name = 'Datetime'

        self.last_positions_dt = self.df_positions.index[-1]

    def update_pv(self):

        pv = DataFrame(self.api.get_portfolio_history(period='1M',timeframe='1H'))

        pv['timestamp'] = pv['timestamp'].apply(lambda x: datetime.fromtimestamp(x))
        pv = pv.rename(columns={'timestamp':'Datetime'}).set_index('Datetime')

        self.df_pv = self.df_pv.append(pv)
        self.df_pv = self.df_pv[~self.df_pv.index.duplicated(keep='last')].sort_index()


    def update_entries(self):

        self.load_signal()

        if self.is_existing_pt():

            self.load_entries()

            self.update_positions()

            self.update_pv()

            self.record_existing_open_orders_and_new_orders()

            self.save_entries()

        else:

            self.make_result_dir()

            self.record_new_orders()

            self.df_positions = DataFrame()

            self.df_saved_predictions = DataFrame()

            self.df_pv = DataFrame()

            self.save_entries()
