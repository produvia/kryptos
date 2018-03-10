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


def get_start_geo(num_plots, cols=1):
    start = int(str(num_plots) + str(cols) + '1')
    return start


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
    if name is None:
        name = 'Strategy'
    ax1 = plt.subplot(pos)
    ax1.set_ylabel('Percent Return (%)')
    res = results.loc[:, ['algorithm_period_return']]
    ax1.plot(res, label=name)


def plot_benchmark(results, pos=211,):

    ax = plt.subplot(pos)
    bench = results.loc[:, ['benchmark_period_return']]
    ax.plot(bench, label='Benchmark', linestyle='--')


def plot_metric(results, metric, pos, y_label=None, label=None, add_mean=False, **kw):
    if y_label is None:
        y_label = '{}'.format(metric.replace('_', '\n').title())

    ax = plt.subplot(pos)
    ax.set_ylabel(y_label)
    res = results.loc[:, [metric]]
    ax.plot(res, label=label, **kw)

    if add_mean:
        mean = [np.mean(res) for i in res.index]
        ax.plot(res, label=label)
        ax.plot(res.index, mean, linestyle='--', label='mean')

    return ax


def plot_points(results, pos, y_val=None, label=None, marker='o', color='green'):
    ax = plt.subplot(pos)
    ax.scatter(
        results.index.to_pydatetime(),
        results.loc[results.index, y_val],
        marker=marker,
        s=100,
        c=color,
        label=label
    )


def plot_buy_sells(results, pos, y_val=None):
    # Plot the price increase or decrease over time.

    if y_val is None:
        y_val = 'price'
        ax = plot_metric(results, 'price', pos, y_label='Buy/Sells')

    else:  # dont plot price if using other y_val
        ax = plt.subplot(pos)

    transaction_df = extract_transactions(results)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df['amount'] > 0]
        sell_df = transaction_df[transaction_df['amount'] < 0]
        ax.scatter(
            buy_df.index.to_pydatetime(),
            results.loc[buy_df.index, y_val],
            marker='^',
            s=100,
            c='green',
            label=''
        )
        ax.scatter(
            sell_df.index.to_pydatetime(),
            results.loc[sell_df.index, y_val],
            marker='v',
            s=100,
            c='red',
            label=''
        )
