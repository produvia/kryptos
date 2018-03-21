import talib as ta
import matplotlib.pyplot as plt

from catalyst.api import record

from logbook import Logger
from crypto_platform.utils import viz
from crypto_platform.strategy.indicators import Indicator

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


class MA(Indicator):
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
        super(MA, self).__init__()
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



