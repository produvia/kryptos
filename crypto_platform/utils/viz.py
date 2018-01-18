import matplotlib.pyplot as plt
import numpy as np
from catalyst.exchange.utils.stats_utils import extract_transactions, get_pretty_stats
from logbook import Logger

log = Logger('Viz')

def show_plot():
    """Prevents crashing when scrolling on macOS"""
    while True:
        try:
            plt.show()
        except UnicodeDecodeError:
            continue
        break


def add_legend():
    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), fancybox=True, shadow=True, ncol=5)


def plot_portfolio(context, results, algo_name=None):
    # Get the base_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    base_currency = exchange.base_currency.upper()

    # First chart: Plot portfolio value using base_currency
    ax = plt.subplot(211)

    val = results.loc[:, ['portfolio_value']]
    ax.plot(val, label=algo_name)


    ax.set_ylabel('Portfolio Value\n({})'.format(base_currency))
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))
    return ax


def plot_percent_return(context, results, algo_name=None, share_x=None):
    ax1 = plt.subplot(211)
    ax1.set_ylabel('Percent Return (%)')
    res = results.loc[:, ['algorithm_period_return']]
    ax1.plot(res, label=algo_name)

def plot_benchmark(results, ax=None):
    if ax is None:
        ax = plt.subplot(211)
    bench = results.loc[:, ['benchmark_period_return']]
    ax.plot(bench, label='benchmark_period_return', linestyle='--')


def plot_metrics(context, results, metrics, algo_name=None):
    if len(metrics) == 0:
        metrics = list(results)
    log.info(metrics)
    fig, ax = plt.subplots(len(metrics), 1, sharex=True)

    if algo_name is not None:
        title = '{}\nPerformance Metrics'.format(algo_name.replace('_', ' ').title())
        fig.suptitle(title)

    try:
        m_plots = zip(ax, metrics)
    except TypeError:
        ax = plt.subplot(111)
        m_plots = [(ax, metrics[0])]

    for ax, m in m_plots:
        ax.set_ylabel('{}'.format(m.replace('_', ' ').title()))
        try:
            res = results.loc[:, [m]]
            mean = [np.mean(res) for i in res.index]
            ax.plot(res)
            ax.plot(res.index, mean, linestyle='--', label='mean')
        except ValueError:
            log.warn('Skipping {} because not formatted as array'.format(m))
            log.warn(type(res))

        except KeyError:
            log.warn('Skipping {} because it missing from the results'.format(m))


def plot_leverage(context, results, share_x=False):
    ax = plt.subplot(412, sharex=ax1)
    results[['leverage']].plot(ax=ax)
    ax.set_ylabel('Leverage ')


def plot_cash(results):
    ax = plt.subplot(413)
    results[['cash']].plot(ax=ax)
    ax.set_ylabel('Cash (USD)')
