""" This script simply runs each algorithim within algos/single_asset/
The recorded results are saved to a csv file  and as a pickled pandas Dataframe
in scripts/performance_results
"""


import os
import tempfile
from catalyst import run_algorithm
from catalyst.api import record

from logbook import Logger
from crypto_platform.utils import load, outputs, viz
from crypto_platform.config import CONFIG

import matplotlib.pyplot as plt
import click

log = Logger ('Strategy Runner')


def get_output_file(algo):
    perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(perf_dir, algo.NAMESPACE)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = '{}_{}_{}'.format(CONFIG.ASSET, CONFIG.BUY_EXHANGE, CONFIG.DATA_FREQUENCY)
    return os.path.join(algo_dir, file_specs)


def record_data(context, data):
     # Let's keep the price of our asset in a more handy variable
    price = data.current(context.asset, 'price')

    # Save values for later inspection
    record(price=price, cash=context.portfolio.cash)


@click.command()
def run():
    for algo in load.load_algos():
        if algo is None:
            continue
        log.info('Running {}'.format(algo.NAMESPACE))
        algo.CONFIG = CONFIG

        def handle_data(context, data):
           record_data(context, data)
           algo.handle_data(context, data)

        def analyze(context, results):
            viz.plot_portfolio(context, results, algo.NAMESPACE)
            output_file = get_output_file(algo) + '.csv'
            log.info('Dumping result csv to {}'.format(output_file))
            outputs.dump_to_csv(output_file, results)


        run_algorithm(
            capital_base=CONFIG.CAPITAL_BASE,
            data_frequency=CONFIG.DATA_FREQUENCY,
            initialize=algo.initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name=CONFIG.BUY_EXHANGE,
            algo_namespace=algo.NAMESPACE,
            base_currency=CONFIG.BASE_CURRENCY,
            start=CONFIG.START,
            end=CONFIG.END,
            output=get_output_file(algo) + '.p'
        )
        log.info('Run completed for {}'.format(algo.NAMESPACE))

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
    plt.show()


if __name__ == '__main__':
    run()
