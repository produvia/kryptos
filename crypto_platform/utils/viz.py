from os.path import basename
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.finance import candlestick_ohlc
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.exchange.utils.stats_utils import extract_transactions, get_pretty_stats


def plot_portfolio(context, perf, algo_name):
    # Get the base_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    base_currency = exchange.base_currency.upper()

    # First chart: Plot portfolio value using base_currency
    ax = plt.subplot(211)
    # ax.set_title(algo_name)
    # ax.legend()

    val = perf.loc[:, ['portfolio_value']]
    ax.plot(val, label=algo_name)

    ax.set_ylabel('Portfolio Value\n({})'.format(base_currency))
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))


def plot_percent_return(context, results, algo_name=None, share_x=None):
    ax1 = plt.subplot(311)
    ax1.set_ylabel('Percent Return (%)')
    res = results.loc[:, ['algorithm_period_return']]
    ax1.plot(res, label=algo_name)

def plot_metrics_over_time(results, metrics):
    print(results.index)
    print(results.columns)
    row_len = len(metrics)
    idx = 1

    for m in metrics:
        ax = plt.subplot(row_len, 1, idx)
        ax.set_ylabel('{}'.format(m.replace('_', ' ').title()))
        res = results.loc[:, [m]]
        ax.plot(res)
        idx += 1


def plot_benchmark(results):
    ax = plt.subplot(311)
    bench = results.loc[:, ['benchmark_period_return']]
    ax.plot(bench, label='benchmark_period_return')


def plot_leverage(context, results, share_x=False):
    ax = plt.subplot(412, sharex=ax1)
    results[['leverage']].plot(ax=ax)
    ax.set_ylabel('Leverage ')


def plot_cash(results):
    ax = plt.subplot(413)
    results[['cash']].plot(ax=ax)
    ax.set_ylabel('Cash (USD)')
