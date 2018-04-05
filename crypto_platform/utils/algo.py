from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError
from logbook import Logger
import pandas as pd

from crypto_platform.strategy import DEFAULT_CONFIG as CONFIG
from crypto_platform.utils import load

log = Logger('AlgoFactory')


def initialze_from_config(context):
    context.asset = symbol(CONFIG['ASSET'])
    context.market = symbol(CONFIG['ASSET'])
    set_benchmark(context.asset)

    context.ORDER_SIZE = 10
    context.SLIPPAGE_ALLOWED = 0.05
    context.BARS = 365

    context.errors = []

    for k, v in CONFIG.items():
        if '__' not in k:
            setattr(context, k, v)


def record_data(context, data, data_manager=None):
    price = data.current(context.asset, 'price')
    cash = context.portfolio.cash

    data_payload = {}
    if data_manager is not None:
        data_payload = data_manager.record_data(context, data)

    # Save values for later inspection
    record(price=price, cash=cash, **data_payload)

    # Get price, open, high, low, close
    prices = data.history(
        context.asset,
        bar_count=context.BARS,
        fields=['price', 'open', 'high', 'low', 'close'],
        frequency='1d')

    # Save the prices and analysis to send to analyze
    context.prices = prices
    context.price = data.current(context.asset, 'price')



def run_algo(initialize, handle_data, analyze):
    try:
        run_algorithm(
            capital_base=CONFIG['CAPITAL_BASE'],
            data_frequency=CONFIG['DATA_FREQ'],
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name=CONFIG['EXCHANGE'],
            base_currency=CONFIG['BASE_CURRENCY'],
            start=pd.to_datetime(CONFIG['START'], utc=True),
            end=pd.to_datetime(CONFIG['END'], utc=True),
        )
    except PricingDataNotLoadedError:
        log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)
