from pickle import TRUE
from pandas import read_csv, to_datetime, MultiIndex, merge, concat, qcut,  DataFrame, factorize
from numpy import array
from functools import reduce
import talib
import lightgbm as lgb


class signal():

    def __init__(self, name, data_path, ticker) -> None:

        self.name = name
        self.data_path = data_path
        self.ticker = ticker

    def load_OHLCV_data(self):

        df_data = read_csv(f'{self.data_path}/{self.ticker}.csv')
        self.index_name = df_data.columns[0]
        df_data[self.index_name] = to_datetime(df_data[self.index_name])
        df_data.set_index(self.index_name, inplace=True)

        self.data = df_data

    def load_Multi_tickers_OHLCV_data(self, hist_length):

        dfs = []

        for tic in self.ticker:

            df = read_csv(f'{self.data_path}/{tic}.csv')
            df['Date'] = to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df = df.iloc[-hist_length:,:]
            df.columns = MultiIndex.from_product([[tic], df.columns])
            dfs.append(df)

        self.data = reduce(lambda x, y: merge(
            left=x, right=y, left_index=True, right_index=True, how='inner'), dfs)

    def get_last_trigger(self):

        triggers = self.data.loc[self.data[f'{self.ticker}_{self.name}'] != 0, :].copy(
        )

        return triggers.index[-1].replace(tzinfo=None), triggers[f'{self.ticker}_{self.name}'].iloc[-1]

    def get_last_data_dt(self):

        return self.data.index[-1].replace(tzinfo=None)

    def get_predictions(self):

        return self.predictions


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


class SectorRankSignal(signal):

    def __init__(self, name, data_path, ticker, **kwargs) -> None:
        super().__init__(name, data_path, ticker)

        self.num_long = kwargs['num_long']
        self.num_short = kwargs['num_short']
        self.lookahead = kwargs['lookahead']
        self.hist_length = kwargs['load_data_history_length']

    def load_data(self):

        self.load_Multi_tickers_OHLCV_data(self.hist_length)
        self.data.index = self.data.index.rename('date')

        sec_data = []
        for t in self.data.columns.get_level_values(0).unique():

            sec_data.append(self.data[t].assign(ticker=t))

        self.prices = concat(sec_data, axis=0)
        self.prices = self.prices.set_index('ticker', append=True)
        self.prices = self.prices.swaplevel()
        self.prices = (self.prices.unstack('ticker')
                       .sort_index()
                       .ffill(limit=5)
                       .dropna(axis=1)
                       .stack('ticker')
                       .swaplevel())

    def compute_features(self):

        # returns and relative returns
        intervals = [1, 5, 10, 21, 63]
        returns = []
        by_sym = self.prices.groupby(level='ticker').Close
        for t in intervals:
            ret = by_sym.pct_change(t)
            rel_perc = (ret.groupby(level='date')
                        .apply(lambda x: qcut(x, q=5, labels=False, duplicates='drop')))
            returns.extend(
                [ret.to_frame(f'ret_{t}'), rel_perc.to_frame(f'ret_rel_perc_{t}')])
        returns = concat(returns, axis=1)

        # technical indicators
        ppo = self.prices.groupby(level='ticker').Close.apply(
            talib.PPO).to_frame('PPO')
        natr = self.prices.groupby(level='ticker', group_keys=False).apply(
            lambda x: talib.NATR(x.High, x.Low, x.Close)).to_frame('NATR')
        rsi = self.prices.groupby(level='ticker').Close.apply(
            talib.RSI).to_frame('RSI')

        def get_bollinger(x):
            u, m, l = talib.BBANDS(x)
            return DataFrame({'u': u, 'm': m, 'l': l})
        bbands = self.prices.groupby(level='ticker').Close.apply(get_bollinger)
        self.data = concat(
            [self.prices, returns, ppo, natr, rsi, bbands], axis=1)
        self.data['bbl'] = self.data.Close.div(self.data.l)
        self.data['bbu'] = self.data.u.div(self.data.Close)
        self.data = self.data.drop(['u', 'm', 'l'], axis=1)

        self.data = self.data.drop(self.prices.columns, axis=1)
        self.data = self.data.reset_index(level='date')
        self.data['date'] = to_datetime(self.data['date'])
        self.data = self.data.set_index('date', append=True)

        dates = self.data.index.get_level_values('date')
        self.data['weekday'] = dates.weekday
        self.data['month'] = dates.month
        self.data['year'] = dates.year

    def compute_predictions(self):

        categoricals = ['year', 'weekday', 'month']
        for feature in categoricals:
            self.data[feature] = factorize(self.data[feature], sort=True)[0]

        test_idx = MultiIndex.from_product([self.data.index.get_level_values(
            'ticker').unique(), [self.data.index.get_level_values('date')[-10]]])
        test_set = self.data.loc[test_idx, :]
        # y_test = test_set.loc[:, label].to_frame('y_test')
        predictions = []
        for i in range(1, 9):
            model = lgb.Booster(model_file=f'models/saved/model_{i}.txt')
            y_pred = model.predict(test_set.loc[:, model.feature_name()])
            predictions.append(y_pred)

        df_pred = DataFrame(array(predictions).transpose(
        ), index=test_idx.get_level_values('ticker'), columns=list(range(8)))
        self.predictions = (df_pred.mean(axis=1).rank().sub(1).to_frame('Rank')
            .assign(date=self.data.index.get_level_values('date')[-1])
            .set_index('date', append=True)
            .merge(self.prices.groupby('ticker').Close.tail(1).to_frame('Close'), left_index=True, right_index=True)
            .sort_values(by='Rank')
            .assign(side=(['buy']*self.num_long + ['Neu']*(len(self.ticker) - self.num_long - self.num_short) + ['sell']*self.num_short)))

    def compute_signal(self):

        self.load_data()
        self.compute_features()
        self.compute_predictions()

        return self.data

    def compute_backtest(self):
        pass



signal_map = {
    'MomentumCrossoverSignal': MomentumCrossoverSignal,
    'SectorRankSignal': SectorRankSignal
}
