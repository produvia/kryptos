# From catalyst examples
import pandas as pd
import talib
from logbook import Logger, INFO

from catalyst import run_algorithm
from catalyst.api import symbol, record
from catalyst.exchange.utils.stats_utils import get_pretty_stats, \
    extract_transactions

CONFIG = None
NAMESPACE = 'simple_loop'

log = Logger(NAMESPACE, level=INFO)


def initialize(context):
    log.info('initializing')
    context.asset = symbol(CONFIG.ASSET)
    context.base_price = None


def handle_data(context, data):
    log.info('handling bar: {}'.format(data.current_dt))

    price = data.current(context.asset, 'close')
    log.info('got price {price}'.format(price=price))

    prices = data.history(
        context.asset,
        fields='price',
        bar_count=20,
        frequency='30T'
    )
    last_traded = prices.index[-1]
    log.info('last candle date: {}'.format(last_traded))

    rsi = talib.RSI(prices.values, timeperiod=14)[-1]
    log.info('got rsi: {}'.format(rsi))

    # If base_price is not set, we use the current value. This is the
    # price at the first bar which we reference to calculate price_change.
    if context.base_price is None:
        context.base_price = price

    price_change = (price - context.base_price) / context.base_price
    cash = context.portfolio.cash

    # Now that we've collected all current data for this frame, we use
    # the record() method to save it. This data will be available as
    # a parameter of the analyze() function for further analysis.
    record(
        price=price,
        price_change=price_change,
        cash=cash
    )


