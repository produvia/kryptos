from os.path import basename
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.finance import candlestick_ohlc
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.exchange.utils.stats_utils import extract_transactions


def plot_portfolio(context, perf, algo_name):
    # Get the base_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    base_currency = exchange.base_currency.upper()

    # create own

    # First chart: Plot portfolio value using base_currency
    ax = plt.subplot(411)
    # ax.set_title(algo_name)
    # ax.legend()

    val = perf.loc[:, ['portfolio_value']]
    ax.plot(val, label=algo_name)

    ax.set_ylabel('Portfolio Value\n({})'.format(base_currency))
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

