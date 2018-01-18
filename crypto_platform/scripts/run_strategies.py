""" This script simply runs each algorithim within algos/single_asset/
The recorded results are saved to a csv file  and as a pickled pandas Dataframe
in scripts/performance_results
"""

from catalyst import run_algorithm
from catalyst.api import record, symbol

from logbook import Logger
from crypto_platform.utils import load, outputs, viz
from crypto_platform.config import CONFIG
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

import matplotlib.pyplot as plt
import click

log = Logger('Strategy Runner')


@click.command()
def run():
    for algo in load.load_algos():
        if algo is None:
            continue
        log.info('Running {}'.format(algo.NAMESPACE))
        algo.CONFIG = CONFIG

        def initialize(context):
            context.ASSET_NAME = CONFIG.ASSET
            context.asset = symbol(context.ASSET_NAME)
            algo.initialize(context)

        def handle_data(context, data):
            price = data.current(context.asset, 'price')
            record(price=price, cash=context.portfolio.cash)
            algo.handle_data(context, data)

        def analyze(context, results):
            viz.plot_portfolio(context, results, algo.NAMESPACE)
            output_file = outputs.get_output_file(algo, CONFIG) + '.csv'
            log.info('Dumping result csv to {}'.format(output_file))
            outputs.dump_to_csv(output_file, results)

        try:
            run_algorithm(
                capital_base=CONFIG.CAPITAL_BASE,
                data_frequency=CONFIG.DATA_FREQUENCY,
                initialize=initialize,
                handle_data=handle_data,
                analyze=analyze,
                exchange_name=CONFIG.BUY_EXCHANGE,
                algo_namespace=algo.NAMESPACE,
                base_currency=CONFIG.BASE_CURRENCY,
                start=CONFIG.START,
                end=CONFIG.END,
                output=outputs.get_output_file(algo, CONFIG) + '.p'
            )
        except PricingDataNotLoadedError:
            log.info('Ingesting required exchange bundle data')
            load.ingest_exchange(CONFIG)
        log.info('Run completed for {}'.format(algo.NAMESPACE))

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
    viz.show_plot()


if __name__ == '__main__':
    run()
