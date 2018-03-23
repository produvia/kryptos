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
    def __init__(self, name, **kw):
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
        self.kw = kw

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
        self.outputs = self.func(df, **self.kw)

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
        if ignore is None:
            ignore = []
        for col in [c for c in list(self.outputs) if c not in ignore]:
            log.error(col)
            ax = viz.plot_column(results, col, pos, y_label=y_label, label=col)
        plt.legend()
        return ax

    @property
    def signals_buy(self):
        """Used to define conditions for buy signal"""
        pass

    @property
    def signals_sell(self):
        """Used to define conditions for buy signal"""
        pass


class BBANDS(TAIndicator):
    def __init__(self, matype=ta.MA_Type.T3):
        super(BBANDS, self).__init__('BBANDS', matype=matype)

    def plot(self, results, pos):
        super().plot(results, pos)

    @property
    def current_price(self):
        return self.data.close[-1]

    @property
    def signals_buy(self):
        if self.current_price > self.outputs.upperband[-1]:
            return True
        return False

    @property
    def signals_sell(self):
        if self.current_price < self.outputs.lowerband[-1]:
            return True
        return False


class SAR(TAIndicator):
    def __init__(self):
        super(SAR, self).__init__('SAR')

    @property
    def current_price(self):
        return self.data.close[-1]

    @property
    def signals_buy(self):
        return self.current_price > self.outputs.SAR[-1]

    @property
    def signals_sell(self):
        if self.current_price < self.outputs.SAR[-1]:
            log.info('Closing position due to PSAR')
            return True
        return False


class MACD(TAIndicator):

    def __init__(self):
        super(MACD, self).__init__('MACD')

    def plot(self, results, pos):
        super().plot(results, pos, ignore=['macdhist'])
        viz.plot_bar(results, 'macdhist', pos)

    @property
    def signals_buy(self):
        return self.outputs.macd[-1] > self.outputs.macdsignal[-1]

    @property
    def signals_sell(self):
        return self.outputs.macd[-1] < self.outputs.macdsignal[-1]


class MACDFIX(TAIndicator):

    def __init__(self):
        super(MACDFIX, self).__init__('MACDFIX')

    def plot(self, results, pos):
        super().plot(results, pos, ignore=['macdhist'])
        viz.plot_bar(results, 'macdhist', pos)

    @property
    def signals_buy(self):
        return self.outputs.macd[-1] > self.outputs.macdsignal[-1]

    @property
    def signals_sell(self):
        return self.outputs.macd[-1] < self.outputs.macdsignal[-1]


class OBV(TAIndicator):
    def __init__(self):
        super(OBV, self).__init__('OBV')

    @property
    def signals_buy(self):
        log.error('checking obv bs')
        log.error('{} > {} ??'.format(self.outputs.OBV[-1], self.outputs.OBV[-2]))
        return self.outputs.OBV[-1] > self.outputs.OBV[-2]

    @property
    def signals_sell(self):
        return self.outputs.OBV[-1] < self.outputs.OBV[-2]


class RSI(TAIndicator):
    def __init__(self, timeperiod=14):
        super(RSI, self).__init__('RSI', timeperiod=timeperiod)

    def record(self):
        super().record()
        record(overbought=self.overbought, oversold=self.oversold)

    def plot(self, results, pos):
        y_label = 'RSI'
        ax = viz.plot_column(results, 'RSI', pos, y_label=y_label, label='RSI')

        overbought_line = [CONFIG.RSI_OVER_BOUGHT for i in results.index]
        oversold_line = [CONFIG.RSI_OVER_SOLD for i in results.index]
        ax.plot(results.index, overbought_line)
        ax.plot(results.index, oversold_line)

        overboughts = results[results['overbought']]
        oversolds = results[results['oversold']]
        viz.plot_points(overboughts, pos, y_val='RSI', color='red', label='overbought')
        viz.plot_points(oversolds, pos, y_val='RSI', label='oversold')

        plt.legend()

    @property
    def overbought(self):
        # RSI OVER BOUGHT & Decreasing
        return self.outputs.RSI[-2] >= CONFIG.RSI_OVER_BOUGHT and self.outputs.RSI[-1] < CONFIG.RSI_OVER_BOUGHT

    @property
    def oversold(self):
        # RSI OVER SOLD & Increasing
        return self.outputs.RSI[-2] <= CONFIG.RSI_OVER_SOLD and self.outputs.RSI[-1] > CONFIG.RSI_OVER_SOLD

    @property
    def signals_buy(self):
        # crosses to above oversold
        return self.oversold

    @property
    def signals_sell(self):
        # crosses to below overbought
        return self.overbought


class STOCH(TAIndicator):
    """docstring for STOCH"""

    def __init__(self, rsi_period):
        super(STOCH, self).__init__('STOCH')

    def record(self):
        super().record()
        record(stoch_overbought=self.overbought, stoch_oversold=self.oversold)

    def plot(self, results, pos):
        ax = super().plot(results, pos)

        overbought_line = [CONFIG.STOCH_OVER_BOUGHT for i in results.index]
        oversold_line = [CONFIG.STOCH_OVER_SOLD for i in results.index]

        ax.plot(results.index, overbought_line)
        ax.plot(results.index, oversold_line)

        overboughts = results[results['stoch_overbought']]
        oversolds = results[results['stoch_oversold']]
        viz.plot_points(overboughts, pos, y_val='slowd', color='red', label='overbought')
        viz.plot_points(oversolds, pos, y_val='slowk', label='oversold')

        plt.legend()

    @property
    def overbought(self):
        return self.outputs.slowd[-2] > CONFIG.STOCH_OVER_BOUGHT and self.outputs.slowd[-1] < self.outputs.slowd[-2]

    @property
    def oversold(self):
        return self.outputs.slowd[-2] < CONFIG.STOCH_OVER_SOLD and self.outputs.slowd[-1] > self.outputs.slowd[-2]

    @property
    def signals_buy(self):
        return self.oversold

    @property
    def signals_sell(self):
        return self.overbought


# class SMA(TAIndicator):
#     def __init__(self, timeperiod=30):
#         super(SMA, self).__init__('SMA', timeperiod=timeperiod)

#     def plot(self, results, pos):
#         viz.plot_column(results, 'price', pos)
#         super().plot(results, pos)

    # def signals_buy(self):
    #     return self.fast > self.slow

    # def signals_sell(self):
    #     return self.slow

