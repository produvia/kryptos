import numpy as np
from logbook import Logger

log = Logger('SIGNALS')


def cross_above(signal_series, trigger):
    if isinstance(trigger, int):
        trigger = [trigger] * 3
    return signal_series[-2] <= trigger[-2] and signal_series[-1] > trigger[-1]


def cross_below(signal_series, trigger):
    if isinstance(trigger, int):
        trigger = [trigger] * 3
    return signal_series[-2] >= trigger[-2] and signal_series[-1] < trigger[-2]


def increasing(series, period=4):
    arr = series[period * -1:]
    return np.all(np.diff(arr) > 0)


def decreasing(series, period=4):
    arr = series[period * -1:]
    return np.all(np.diff(arr) < 0)
