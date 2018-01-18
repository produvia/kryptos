import os
import tempfile
from catalyst import run_algorithm
from catalyst.api import record, set_benchmark

from logbook import Logger
from crypto_platform.utils import load, outputs, viz
from crypto_platform.config import CONFIG

import matplotlib.pyplot as plt
import click

log = Logger('Benchmark Runner')


def record_data(context, data):
     # Let's keep the price of our asset in a more handy variable
    price = data.current(context.asset, 'price')

    # Save values for later inspection
    record(price=price, cash=context.portfolio.cash)


@click.command()
@click.argument('algo_name')
def benchmark(algo_name):

    for a in load.load_algos():
        if a.NAMESPACE == str(algo_name):
            algo = a
            break
    log.info('Benchmarking {}'.format(algo.NAMESPACE))
    algo.CONFIG = CONFIG

    def initialize(context):
        algo.initialize(context)
        set_benchmark(context.asset)

    def handle_data(context, data):
        record_data(context, data)
        algo.handle_data(context, data)

    def analyze(context, results):
        viz.plot_percent_return(context, results, algo.NAMESPACE)
        viz.plot_benchmark(results)

    run_algorithm(
        capital_base=CONFIG.CAPITAL_BASE,
        data_frequency=CONFIG.DATA_FREQUENCY,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name=CONFIG.BUY_EXHANGE,
        algo_namespace=algo.NAMESPACE,
        base_currency=CONFIG.BASE_CURRENCY,
        start=CONFIG.START,
        end=CONFIG.END,
        output=outputs.get_output_file(algo, CONFIG) + '.p'
    )
    log.info('Run completed for {}'.format(algo.NAMESPACE))

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
    plt.show()


if __name__ == '__main__':
    run()
