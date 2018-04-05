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
from crypto_platform.strategy.signals import utils

log = Logger('INDICATOR')


def get_indicator(name, **kw):
    subclass = globals().get(name.upper())
    if subclass is not None:
        return subclass(**kw)

    return TAIndicator(name, **kw)


class TAIndicator(AbstractIndicator):
    def __init__(self, name, **kw):
        super().__init__(name, **kw)
        """Factory for creating an indicator using the ta-lib library

        The costructor is passed the name of the indicator.
        The calculation is performed at each iteration and is recored
        and plotted based on the ta-lib function's outputs.

        To signal trade opportunities, subclassed objects can implement
        the signals_buy and signals_sell methods.

        Extends:
            Indicator): def __init__(self, name
        """


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
        self.outputs = self.func(df, **self.params)
        if len(self.outputs) == 1 and self.label is not None:
            self.outputs.columns = [self.label]

        if isinstance(self.outputs, pd.Series):
            self.outputs = self.outputs.to_frame(self.label)

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
    def __init__(self, **kw):
        super().__init__('BBANDS', **kw)

    def plot(self, results, pos):
        super().plot(results, pos)

    @property
    def current_price(self):
        return self.data.close[-1]

    @property
    def signals_buy(self):
        return utils.cross_above(self.data.close, self.outputs.upperband)

    @property
    def signals_sell(self):
        return utils.cross_below(self.data.close, self.outputs.lowerband)


class SAR(TAIndicator):
    def __init__(self, **kw):
        super(SAR, self).__init__('SAR', **kw)

    def plot(self, results, pos):
        viz.plot_column(results, 'price', pos)
        viz.plot_as_points(results, self.name, pos, y_val='SAR', color='black')

    @property
    def current_price(self):
        return self.data.close[-1]

    @property
    def signals_buy(self):
        return self.outputs.SAR[-1] == self.data.low[-2]

    @property
    def signals_sell(self):
        bearish = utils.cross_below(self.data.close, self.outputs.SAR)
        if bearish:
            log.info('Closing position due to PSAR')
        return bearish


class MACD(TAIndicator):

    def __init__(self, **kw):
        super(MACD, self).__init__('MACD', **kw)

    def plot(self, results, pos):
        super().plot(results, pos, ignore=['macdhist'])
        viz.plot_bar(results, 'macdhist', pos)

    @property
    def signals_buy(self):
        return utils.cross_above(self.outputs.macd, self.outputs.macdsignal)

    @property
    def signals_sell(self):
        return utils.cross_below(self.outputs.macd, self.outputs.macdsignal)


class MACDFIX(TAIndicator):

    def __init__(self, **kw,):
        super(MACDFIX, self).__init__('MACDFIX', **kw)

    def plot(self, results, pos):
        super().plot(results, pos, ignore=['macdhist'])
        viz.plot_bar(results, 'macdhist', pos)

    @property
    def signals_buy(self):
        return utils.cross_above(self.outputs.macd, self.outputs.macdsignal)

    @property
    def signals_sell(self):
        return utils.cross_below(self.outputs.macd, self.outputs.macdsignal)


class OBV(TAIndicator):
    def __init__(self, **kw):
        super(OBV, self).__init__('OBV', **kw)

    @property
    def signals_buy(self):
        return utils.increasing(self.outputs.OBV)

    @property
    def signals_sell(self):
        return utils.decreasing(self.outputs.OBV)


class RSI(TAIndicator):
    def __init__(self, timeperiod=14, **kw):
        super(RSI, self).__init__('RSI', timeperiod=timeperiod, **kw)

    def record(self):
        super().record()
        record(overbought=self.overbought, oversold=self.oversold)

    def plot(self, results, pos):
        y_label = 'RSI'
        ax = viz.plot_column(results, 'RSI', pos, y_label=y_label, label='RSI')

        overbought_line = [CONFIG.RSI_OVERBOUGHT for i in results.index]
        oversold_line = [CONFIG.RSI_OVERSOLD for i in results.index]
        ax.plot(results.index, overbought_line)
        ax.plot(results.index, oversold_line)

        overboughts = results[results['overbought']]
        oversolds = results[results['oversold']]
        viz.mark_on_line(results, pos, y_val='RSI', color='red', label='overbought')
        viz.mark_on_line(oversolds, pos, y_val='RSI', label='oversold')

        plt.legend()

    @property
    def overbought(self):
        return utils.cross_above(self.outputs.RSI, CONFIG.RSI_OVERBOUGHT)

    @property
    def oversold(self):
        return utils.cross_below(self.outputs.RSI, CONFIG.RSI_OVERSOLD)

    @property
    def signals_buy(self):
        return self.oversold

    @property
    def signals_sell(self):
        return self.overbought


class STOCH(TAIndicator):
    """docstring for STOCH"""

    def __init__(self, **kw):
        super(STOCH, self).__init__('STOCH', **kw)

    def record(self):
        super().record()
        record(stoch_overbought=self.overbought, stoch_oversold=self.oversold)

    def plot(self, results, pos):
        ax = super().plot(results, pos)

        overbought_line = [CONFIG.STOCH_OVERBOUGHT for i in results.index]
        oversold_line = [CONFIG.STOCH_OVERSOLD for i in results.index]

        ax.plot(results.index, overbought_line)
        ax.plot(results.index, oversold_line)

        overboughts = results[results['stoch_overbought']]
        oversolds = results[results['stoch_oversold']]
        viz.mark_on_line(overboughts, pos, y_val='slowd', color='red', label='overbought')
        viz.mark_on_line(oversolds, pos, y_val='slowk', label='oversold')

        plt.legend()

    @property
    def overbought(self):
        return utils.cross_above(self.outputs.slowd, CONFIG.STOCH_OVERBOUGHT)

    @property
    def oversold(self):
        return utils.cross_below(self.outputs.slowd, CONFIG.STOCH_OVERSOLD)
        return self.outputs.slowd[-1] < CONFIG.STOCH_OVERSOLD and utils.increasing(self.outputs.slowd, 2)

    @property
    def signals_buy(self):
        return self.oversold

    @property
    def signals_sell(self):
        return self.overbought

class SMA(TAIndicator):
    def __init__(self, **kw):
        super(SMA, self).__init__('SMA', **kw)

    @property
    def signals_buy(self):
        return utils.increasing(self.outputs.get(self.label))

    @property
    def signals_sell(self):
        return utils.decreasing(self.outputs.get(self.label))
