import numpy as np
import talib as ta
import talib.abstract as ab
import matplotlib.pyplot as plt
import pandas as pd

from catalyst.api import record

from logbook import Logger
from crypto_platform.config import TAConfig as CONFIG
from crypto_platform.utils import viz
from crypto_platform.strategy.indicators import AbstractIndicator

log = Logger('INDICATOR')

def get_indicator(name):
    subclass = globals().get(name)
    if subclass is not None:
        return subclass()

    return TAIndicator(name)


class TAIndicator(AbstractIndicator):
    def __init__(self, name):
        """Factory for creating an indicator using the ta-lib library
        
        The costructor is passed the name of the indicator.
        The calculation is performed at each iteration and is recored
        and plotted based on the ta-lib function's outputs.

        To signal trade opportunities, subclassed objects can implement
        the signals_buy and signals_sell methods.
        
        Extends:
            Indicator): def __init__(self, name
        """
        self.name = name.upper()
        self.data = None
        self.outputs = None

    @property
    def func(self):
        """References the underlying ta-lib function"""
        return getattr(ab, self.name)

    def calculate(self, df, **kw):
        """Applies the indicator calculation on the provided data

        Dataframe must consist of at least one column of OHLCV values.
        Some indicators require only one column, but all are capable of
        receiving all 5 columns.

        For consistency all OHCLV columns should be provided in the dataframe

        Arguments:
            df {pandas.Dataframe} -- OHLCV dataframe
            **kw {[type]} -- [description]
        """
        self.data = df
        self.outputs = self.func(df, **kw)

        if isinstance(self.outputs, pd.Series):
            self.outputs = self.outputs.to_frame(self.name)

    def record(self):
        """Records indicator's output to catalyst results"""
        payload = {}
        for out in self.outputs.columns:
            val = self.outputs[out].iloc[-1]
            payload[out] = val

        record(**payload)

    def plot(self, results, pos, ignore=None):
        """Plots the indicators outputs"""
        y_label = self.name
        for col in [c for c in list(self.outputs) if c not in ignore]:
            log.error(col)
            viz.plot_column(results, col, pos, y_label=y_label, label=col)
        plt.legend()

    @property
    def signals_buy(self):
        """Used to define conditions for buy signal"""
        pass

    @property
    def signals_sell(self):
        """Used to define conditions for buy signal"""
        pass


# class BBANDS(TAIndicator):
#     def __init__(self):
#         super(BBANDS, self).__init__('BBANDS')

#     def plot(self, results, pos):
#         viz.plot_column(results, 'price', pos, label='price')
#         super().plot(results, pos)

#     @property
#     def current_price(self):
#         return self.data.close[-1]

#     @property
#     def signals_buy(self):
#         # log.error('**************************************')
#         # log.error('{} -- {}'.format(self.current_price, self.outputs.upperband[-1]))
#         if self.current_price > self.outputs.upperband[-1]:
#             log.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
#             return True
#         return False

#     @property
#     def signals_sell(self):
#         # log.error('**************************************')

#         if self.current_price < self.outputs.lowerband[-1]:
#             return True
#         return False


# class PSAR(TAIndicator):
#     def __init__(self):
#         super(PSAR, self).__init__('SAR')

#     @property
#     def current_price(self):
#         return self.data.close[-1]

#     @property
#     def signals_buy(self):
#         return self.current_price > self.psar[-1]

#     @property
#     def signals_sell(self):
#         if self.current_price < self.psar[-1]:
#             log.info('Closing position due to PSAR')
#             return True
#         return False


class MACD(TAIndicator):

    def __init__(self):
        super(MACD, self).__init__('MACD')

    def plot(self, results, pos):
        super().plot(results, pos, ignore=['macdhist'])
        viz.plot_hist(results, 'macdhist', pos)

    @property
    def signals_buy(self):
        return self.outputs.macd[-1] > self.outputs.macdsignal[-1]

    @property
    def signals_sell(self):
        return self.outputs.macd[-1] < self.outputs.macdsignal[-1]


# class MACDFIX(MACD):

#     def __init__(self):
#         super(MACD, self).__init__('MACDFIX')


#     # def calculate(self, prices):
#     #     self.macd, self.macd_signal, self.macd_hist = ta.MACDFIX(
#     #         prices.close.as_matrix(), signalperiod=CONFIG.MACD_SIGNAL)

#     #     self.macd_test = np.where((self.macd > self.macd_signal), 1, 0)


# class OBV(TAIndicator):
#     def __init__(self):
#         super(OBV, self).__init__('OBV')

#     @property
#     def signals_buy(self):
#         log.error('checking obv bs')
#         log.error('{} > {} ??'.format(self.obv[-1], self.obv[-2]))
#         return self.outputs.obv[-1] > self.outputs.obv[-2]

#     @property
#     def signals_sell(self):
#         return self.outputs.obv[-1] < self.outputs.obv[-2]


# class RSI(TAIndicator):
#     def __init__(self):
#         super(RSI, self).__init__('RSI')

#     def calculate(self, prices):
#         self.rsi = ta.RSI(prices.close.as_matrix(), CONFIG.RSI_PERIOD)

#     def record(self):
#         record(rsi=self.rsi[-1], overbought=self.overbought, oversold=self.oversold)

#     def plot(self, results, pos):
#         y_label = 'RSI'
#         ax = viz.plot_column(results, 'rsi', pos, y_label=y_label, label='rsi')

#         overbought_line = [CONFIG.RSI_OVER_BOUGHT for i in results.index]
#         oversold_line = [CONFIG.RSI_OVER_SOLD for i in results.index]
#         ax.plot(results.index, overbought_line)
#         ax.plot(results.index, oversold_line)

#         overboughts = results[results['overbought']]
#         oversolds = results[results['oversold']]
#         viz.plot_points(overboughts, pos, y_val='rsi', color='red', label='overbought')
#         viz.plot_points(oversolds, pos, y_val='rsi', label='oversold')

#         plt.legend()

#     @property
#     def overbought(self):
#         # RSI OVER BOUGHT & Decreasing
#         return self.rsi[-2] >= CONFIG.RSI_OVER_BOUGHT and self.rsi[-1] < CONFIG.RSI_OVER_BOUGHT

#     @property
#     def oversold(self):
#         # RSI OVER SOLD & Increasing
#         return self.rsi[-2] <= CONFIG.RSI_OVER_SOLD and self.rsi[-1] > CONFIG.RSI_OVER_SOLD

#     @property
#     def signals_buy(self):
#         # crosses to above oversold
#         return self.rsi[-2] <= CONFIG.RSI_OVER_SOLD and self.rsi[-1] > CONFIG.RSI_OVER_SOLD

#     @property
#     def signals_sell(self):
#         # crosses to below overbought
#         return self.rsi[-2] >= CONFIG.RSI_OVER_BOUGHT and self.rsi[-1] < CONFIG.RSI_OVER_BOUGHT

#     @property
#     def sma_rsi(self):
#         return ta.SMA(self.rsi.as_matrix(), CONFIG.RSI_AVG_PERIOD)

#     @property
#     def sma_fast(self):
#         self.results['sma_fast'] = ta.SMA(self.prices.close.as_matrix(), CONFIG.SMA_FAST)
#         return self.results['sma_fast']

#     @property
#     def sma_slow(self):
#         return ta.SMA(self.pricesclose.as_matrix(), CONFIG.SMA_SLOW)

#     @property
#     def sma_test(self):
#         return np.where(self.sma_fast > self.sma_slow, 1, 0)


# class STOCH(TAIndicator):
#     """docstring for STOCH"""

#     def __init__(self):
#         super(STOCH, self).__init__()

#     def calculate(self, prices):
#         self.stoch_k, self.stoch_d = ta.STOCH(
#             prices.high.as_matrix(), prices.low.as_matrix(),
#             prices.close.as_matrix(), slowk_period=CONFIG.STOCH_K_PERIOD,
#             slowd_period=CONFIG.STOCH_D_PERIOD)

#     def record(self):
#         record(
#             stoch_k=self.stoch_k[-1],
#             stoch_d=self.stoch_d[-1],
#             stoch_overbought=self.overbought,
#             stoch_oversold=self.oversold)

#     def plot(self, results, pos):
#         y_label = 'STOCH'
#         viz.plot_column(results, 'stoch_k', pos, y_label=y_label, label='stoch_k')
#         ax = viz.plot_column(results, 'stoch_d', pos, y_label=y_label, label='stoch_d')

#         overbought_line = [CONFIG.STOCH_OVER_BOUGHT for i in results.index]
#         oversold_line = [CONFIG.STOCH_OVER_SOLD for i in results.index]
#         ax.plot(results.index, overbought_line)
#         ax.plot(results.index, oversold_line)

#         overboughts = results[results['stoch_overbought']]
#         oversolds = results[results['stoch_oversold']]
#         viz.plot_points(overboughts, pos, y_val='stoch_k', color='red', label='overbought')
#         viz.plot_points(oversolds, pos, y_val='stoch_k', label='oversold')

#         plt.legend()

#     @property
#     def overbought(self):
#         return self.stoch_d[-2] > CONFIG.STOCH_OVER_BOUGHT and self.stoch_d[-1] < self.stoch_d[-2]

#     @property
#     def oversold(self):

#         return self.stoch_d[-2] < CONFIG.STOCH_OVER_SOLD and self.stoch_d[-1] > self.stoch_d[-2]

#     @property
#     def signals_buy(self):
#         return self.oversold

#     @property
#     def signals_sell(self):
#         return self.overbought


# class SMA(object):
#     def __init__(self, prices):
#         super(SMA, self).__init__()
#         self.prices = prices
        # self.calculate()

#     def calculate(self):
#         self.slow = ta.SMA(self.prices.close.as_matrix())
#         self.fast = ta.SMA(self.prices.close.as_matrix(), CONFIG.SMA_FAST)

#     def plot(self, results, pos):
#         y_label = 'SMA'
#         ax = viz.plot_column(results, 'sma_slow', pos, y_label=y_label, label='sma_slow')
#         viz.plot_column(results, 'sma_fast', pos, y_label=y_label, label='sma_fast')
#         viz.plot_column(results, 'price', pos, y_label=y_label, label='sma_fast')

#         viz.plot_buy_sells(results, pos, y_val='price' )

#         plt.legend()

#     def record(self):
#         record(sma_slow=self.slow[-1], sma_fast=self.fast[-1])

#     def signals_buy(self):
#         return self.fast > self.slow

#     def signals_sell(self):
#         return self.slow


#     # Stochastics OVER BOUGHT & Decreasing
#     df['stoch_over_bought'] = np.where(
#         (df.stoch_k > CONFIG.STOCH_OVER_BOUGHT) & (
#             df.stoch_k > df.stoch_k.shift(1)), 1, 0)

#     # Stochastics OVER SOLD & Increasing
#     df['stoch_over_sold'] = np.where(
#         (df.stoch_k < CONFIG.STOCH_OVER_SOLD) & (
#             df.stoch_k > df.stoch_k.shift(1)), 1, 0)

#     # Stochastics %K %D
#     # %K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
#     # %D = 3-day SMA of %K
#     df['stoch_k'], df['stoch_d'] = ta.STOCH(
#         prices.high.as_matrix(), prices.low.as_matrix(),
#         prices.close.as_matrix(), slowk_period=CONFIG.STOCH_K,
#         slowd_period=CONFIG.STOCH_D)

#     # Stochastics OVER BOUGHT & Decreasing
#     df['stoch_over_bought'] = np.where(
#         (df.stoch_k > CONFIG.STOCH_OVER_BOUGHT) & (
#             df.stoch_k > df.stoch_k.shift(1)), 1, 0)

#     # Stochastics OVER SOLD & Increasing
#     df['stoch_over_sold'] = np.where(
#         (df.stoch_k < CONFIG.STOCH_OVER_SOLD) & (
#             df.stoch_k > df.stoch_k.shift(1)), 1, 0)


# def stoch_rsi(prices, df):
#     df['fast_k'], df['fast_d'] = ta.STOCHRSI(
#         prices.close.as_matrix(),
#         timeperiod=CONFIG.TIMEPERIOD,
#         fastk_period=CONFIG.FASTK_PERIOD,
#         fastd_period=CONFIG.FASTD_PERIOD,
#         fastd_matype=CONFIG.FASTD_MATYPE)

#     # Stochastics %K %D
#     # %K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
#     # %D = 3-day SMA of %K
#     # df['stoch_k'], df['stoch_d'] = ta.STOCHRSI(
#     #     prices.high.as_matrix(), prices.low.as_matrix(),
#     #     prices.close.as_matrix(), slowk_period=CONFIG.STOCH_K,
#     #     slowd_period=CONFIG.STOCH_D)

#     # Stochastics OVER BOUGHT & Decreasing
#     df['stoch_over_bought'] = np.where(
#         (df.fast_k > CONFIG.STOCH_OVER_BOUGHT) & (
#             df.fast_k > df.fast_k.shift(1)), 1, 0)

#     # Stochastics OVER SOLD & Increasing
#     df['stoch_over_sold'] = np.where(
#         (df.fast_k < CONFIG.STOCH_OVER_SOLD) & (
#             df.fast_k > df.fast_k.shift(1)), 1, 0)
