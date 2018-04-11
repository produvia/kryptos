import numpy as np
from logbook import Logger

log = Logger('SIGNALS')


def cross_above(signal_series, trigger):
    if isinstance(trigger, int):
        trigger = [trigger] * 3
    try:
        return signal_series[-2] <= trigger[-2] and signal_series[-1] > trigger[-1]
    except IndexError:
        log.warn('Not enough data to calculate cross above')
        return False

def cross_below(signal_series, trigger):
    if isinstance(trigger, int):
        trigger = [trigger] * 3
    try:
        return signal_series[-2] >= trigger[-2] and signal_series[-1] < trigger[-2]
    except IndexError:
        log.warn('Not enough data to calculate cross above')
        return False

def increasing(series, period=4):
    arr = series[period * -1:]
    return np.all(np.diff(arr) > 0)


def decreasing(series, period=4):
    arr = series[period * -1:]
    return np.all(np.diff(arr) < 0)

def greater_than(series_1, series_2):
    return series_1[-1] > series_2[-1]

def less_than(series_1, series_2):
    return series_1[-1] < series_2[-1]
