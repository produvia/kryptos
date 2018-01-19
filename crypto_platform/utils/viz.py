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


def plot_portfolio(context, results, name=None, pos=211):
    # Get the base_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    base_currency = exchange.base_currency.upper()

    # First chart: Plot portfolio value using base_currency
    ax = plt.subplot(pos)

    val = results.loc[:, ['portfolio_value']]
    ax.plot(val, label=name)

    ax.set_ylabel('Portfolio Value\n({})'.format(base_currency))
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))


def plot_percent_return(results, name=None, pos=211):
    ax1 = plt.subplot(pos)
    ax1.set_ylabel('Percent Return (%)')
    res = results.loc[:, ['algorithm_period_return']]
    ax1.plot(res, label=name)


def plot_benchmark(results, pos=211,):

    ax = plt.subplot(211)
    bench = results.loc[:, ['benchmark_period_return']]
    ax.plot(bench, label='benchmark_period_return', linestyle='--')


def plot_metrics(context, results, metrics, name=None, pos=111):
    if len(metrics) == 0:
        metrics = list(results)

    fig, ax = plt.subplots(len(metrics), 1, sharex=True)

    if name is not None:
        title = '{}\nPerformance Metrics'.format(name.replace('_', ' ').title())
        fig.suptitle(title)

    try:
        m_plots = zip(ax, metrics)
    except TypeError:
        ax = plt.subplot(pos)
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

        except Exception as e:
            log.warn('Skipping {}'.format(m))
            log.warn(e)

