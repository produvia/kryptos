from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from logbook import Logger
from crypto_platform.utils import load, outputs, viz
from crypto_platform.config import CONFIG

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

    algo = load.load_by_name(algo_name)
    click.echo('Benchmarking {}'.format(algo.NAMESPACE))
    algo.CONFIG = CONFIG


    def initialize(context):
        context.ASSET_NAME = CONFIG.ASSET
        context.asset = symbol(context.ASSET_NAME)
        context.market = symbol(CONFIG.ASSET)
        algo.initialize(context)

        set_benchmark(context.asset)

    def handle_data(context, data):
        record_data(context, data)
        algo.trade_logic(context, data)

    def analyze(context, results):
        viz.plot_percent_return(results, algo.NAMESPACE)
        viz.plot_benchmark(results)
        output_file = outputs.get_output_file(algo, CONFIG) + '.csv'
        log.info('Dumping result csv to {}'.format(output_file))
        viz.plot_buy_sells(results, pos=212)


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
    except PricingDataNotLoadedError as e:
        log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)
        raise e
        

    viz.add_legend()
    viz.show_plot()
    log.info('Run completed for {}'.format(algo.NAMESPACE))


if __name__ == '__main__':
    run()
