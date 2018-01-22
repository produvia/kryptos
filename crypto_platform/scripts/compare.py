from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError


from crypto_platform.utils import load, outputs, viz
from crypto_platform.config import CONFIG
from logbook import Logger

import matplotlib.pyplot as plt
import click

log = Logger('Comparison')


def record_data(context, data):
     # Let's keep the price of our asset in a more handy variable
    price = data.current(context.asset, 'price')

    # Save values for later inspection
    record(price=price, cash=context.portfolio.cash)


@click.command()
@click.argument('algos', nargs=-1)
@click.option('--metrics', '-m', multiple=True, default=None)
def run(algos, metrics):
    click.secho('Comparing {}\n using {}'.format(algos, metrics), fg='white')
    if len(metrics) > 0:
        CONFIG.METRICS = metrics

    RESULTS_FOR_BENCHMARK = None

    for a in algos:
        algo = load.load_by_name(a)
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
            algo.trade_logic(context, data)

        def analyze(context, results):
            viz.plot_percent_return(results, name=algo.NAMESPACE)
            if algos.index(a) == len(algos) - 1:
                viz.plot_benchmark(results)

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

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
