from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol, get_open_orders, order, cancel_order, get_dataset
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from crypto_platform.utils import load, viz
from crypto_platform.analysis.indicators import TAAnalysis
from crypto_platform.config import CONFIG
from crypto_platform.datasets.quandl_data.manager import QuandleDataManager
from logbook import Logger

import click
import matplotlib.pyplot as plt


log = Logger('Blockchain Activity')


qdata = QuandleDataManager()


@click.command()
@click.option('--datasets', '-s', multiple=True)
def run(datasets):
    click.secho('Executing using datasets:\n{}'.format(datasets), fg='white')

    def initialize(context):

        context.ORDER_SIZE = 10
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365

        context.swallow_errors = True
        context.errors = []

        context.ASSET_NAME = CONFIG.ASSET
        context.asset = symbol(context.ASSET_NAME)
        context.market = symbol(CONFIG.ASSET)

        set_benchmark(context.asset)

        context.ta = TAAnalysis()

    def handle_data(context, data):
        date = context.blotter.current_dt.date()

        # TODO grab columns in batches instead of loop
        record_payload = {}
        for col in datasets:
            current_val = qdata.column_by_date(col, date)
            record_payload[col] = current_val
            log.info('{}: {}'.format(col, current_val))

        record(**record_payload)


    def analyze(context, results):
        pos = viz.get_start_geo(len(datasets))
        for d in datasets:
            name = qdata.pretty_title(d)
            viz.plot_metric(results, d, pos=pos, y_label=name, label=name)
            pos += 1
        plt.legend()

    try:
        run_algorithm(
            capital_base=CONFIG.CAPITAL_BASE,
            data_frequency=CONFIG.DATA_FREQUENCY,
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name=CONFIG.BUY_EXCHANGE,
            base_currency=CONFIG.BASE_CURRENCY,
            start=CONFIG.START,
            end=CONFIG.END,
        )
    except PricingDataNotLoadedError:
        log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
