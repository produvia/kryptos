from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError


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
@click.option('--metrics', '-m', multiple=True, default=None)
def run(algo_name, metrics):
    for a in load.load_algos():
        if a.NAMESPACE == str(algo_name):
            algo = a
            break
    # log.info('Benchmarking {}'.format(algo.NAMESPACE))
    if len(metrics) < 0:
        CONFIG.METRICS = metrics
    algo.CONFIG = CONFIG

    def initialize(context):
        log.info('Running {} using {} on {}'.format(algo.NAMESPACE, CONFIG.ASSET, CONFIG.BUY_EXCHANGE))
        context.ASSET_NAME = CONFIG.ASSET
        context.asset = symbol(context.ASSET_NAME)
        context.market = symbol(CONFIG.ASSET)
        algo.initialize(context)

        set_benchmark(context.asset)

    def handle_data(context, data):
        record_data(context, data)
        algo.handle_data(context, data)

    def analyze(context, results):
        viz.plot_metrics(context, results, CONFIG.METRICS, algo_name=algo.NAMESPACE)

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

    viz.show_plot()


if __name__ == '__main__':
    run()
