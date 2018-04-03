import talib as ta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from catalyst.api import record

from logbook import Logger
from crypto_platform.utils import viz
from crypto_platform.strategy.indicators import AbstractIndicator

log = Logger('BASICINDICATOR')


# The "moving average types" are integers, mapping to the TA_MAType enum in the underlying C library:

MA_TYPE_MAP = {
    'SMA': 0,    # Simple Moving Average
    'EMA': 1,    # Exponential Moving Average
    'WMA': 2,    # Weighted Moving Average
    'DEMA': 3,   # Double Exponential Moving Average
    'TEMA': 4,   # Triple Exponential Moving Average
    'TRIMA': 5,  # Triangular Moving Average
    'KAMA': 6,   # Kaufman Adaptive Moving Average
    'MAMA': 7,   # MESA Adaptive Moving Average
    'T3': 8,     # Triple Generalized Double Exponential Moving Average
}


class RELCHANGE(AbstractIndicator):
    def __init__(self, delta_t=4, **kw):
        super().__init__('RELCHANGE', **kw)
        self.delta_t = delta_t

    def calculate(self, trend_series):
        self.data = trend_series

        df = trend_series.to_frame(name='val')
        df['mean'] = df['val'].rolling(self.delta_t).mean()

        df['rel_change'] = df['val'] - df['mean'].shift(periods=1, freq=self.delta_t)
        df['rel_change_ratio'] = df['rel_change'] / df['mean'].shift(periods=1, freq=self.delta_t)
        self.outputs = df

    def record(self):
        record(rel_change=self.outputs.rel_change[-1], rel_change_ratio=self.outputs.rel_change_ratio[-1])


    def plot(self, results, pos, **kw):
        ax = viz.plot_column(results, 'rel_change', pos, label='Relative Change', color='r', **kw)
        ax2 = viz.plot_column(results, 'rel_change_ratio', pos, label='Relative Change Ratio', color='g', twin=ax, **kw)

        viz.add_twin_legends([ax, ax2])

    @property
    def signals_sell(self):
        return self.outputs.rel_change[-1] < 0.0
    @property
    def signals_buy(self):
        return self.outputs.rel_change[-1] > 0.0


class MA(AbstractIndicator):
    """Base Moving Avergae class

        Moving Avergae indicators can be created by initializing this class
        with the desired MA Type and timeperiod, or any of the child classes representing
        the desired MA type

        Available MA_TYPES:
            SMA
            EMA
            WMA
            DEMA
            TEMA
            TRIMA
            KAMA
            MAMA
            T3
    """

    def __init__(self, ma_type, timeperiod):
        super(MA, self).__init__(ma_type.upper())
        self.ma_type = ma_type.upper()
        self.timeperiod = timeperiod

    @property
    def name(self):
        return self.ma_type + str(self.timeperiod)

    @property
    def ma_type_int(self):
        try:
            return MA_TYPE_MAP[self.ma_type]
        except KeyError:
            raise Exception('MA type {} not supported')

    def calculate(self, series):
        self.value = ta.MA(series, timeperiod=self.timeperiod, matype=self.ma_type_int)
        log.error(self.value[-1])

    def record(self):
        payload = {self.name: self.value[-1]}
        record(**payload)

    def plot(self, results, pos, **kw):
        y_label = 'Moving Averages'
        viz.plot_column(results, self.name, pos, y_label=y_label, label=self.name, **kw)
        plt.legend()

    @property
    def signals_buy(self):
        pass

    @property
    def signals_sell(self):
        pass


class SMA(MA):
    def __init__(self, timeperiod=30):
        super(SMA, self).__init__('SMA', timeperiod)
