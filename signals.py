from pickle import TRUE
from pandas import read_csv, to_datetime


class signal():

    def __init__(self, name, data_path, ticker) -> None:

        self.name = name
        self.data_path = data_path
        self.ticker = ticker

    def load_OHLCV_data(self):

        df_data = read_csv(f'{self.data_path}/{self.ticker}.csv')
        self.index_name = df_data.columns[0]
        df_data[self.index_name] = to_datetime(df_data[self.index_name])
        df_data.set_index(self.index_name, inplace=TRUE)

        self.data = df_data

    def get_last_trigger(self):
        
        triggers = self.data[self.data[f'{self.ticker}_{self.name}']!=0,:].copy()
        
        return triggers.index[-1], triggers[f'{self.ticker}_{self.name}'].iloc[-1]

    def get_last_data_dt(self):

        return self.data.index[-1]


class MomentumCrossoverSignal(signal):

    def __init__(self, name, data_path, ticker, **kwargs) -> None:
        super().__init__(name, data_path, ticker)

        self.short_period = kwargs['short_period']
        self.long_period = kwargs['long_period']

    def compute_signal(self):

        self.load_OHLCV_data()

        self.data['sma'] = self.data['Adj Close'].rolling(
            self.short_period).mean()
        self.data['lma'] = self.data['Adj Close'].rolling(
            self.long_period).mean()

        self.data['crossover'] = self.data['sma'] > self.data['lma']

        self.data[f'{self.ticker}_{self.name}'] = self.data['crossover'].astype(
            int).diff()

        return self.data

    


signal_map = {
    'MomentumCrossoverSignal': MomentumCrossoverSignal
}
