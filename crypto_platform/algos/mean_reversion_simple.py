# From catalyst examples

# For this example, we're going to write a simple momentum script.  When the
# stock goes up quickly, we're going to buy; when it goes down quickly, we're
# going to sell.  Hopefully we'll ride the waves.
import os
import tempfile
import time

import numpy as np
import pandas as pd
import talib
from logbook import Logger

from catalyst import run_algorithm
from catalyst.api import symbol, record, order_target_percent, get_open_orders
from catalyst.exchange.utils.stats_utils import extract_transactions
# We give a name to the algorithm which Catalyst will use to persist its state.
# In this example, Catalyst will create the `.catalyst/data/live_algos`
# directory. If we stop and start the algorithm, Catalyst will resume its
# state using the files included in the folder.
from catalyst.utils.paths import ensure_directory

CONFIG = None
NAMESPACE = 'mean_reversion_simple'
log = Logger(NAMESPACE)


# To run an algorithm in Catalyst, you need two functions: initialize and
# handle_data.

def initialize(context):
    # This initialize function sets any data or variables that you'll use in
    # your algorithm.  For instance, you'll want to define the trading pair (or
    # trading pairs) you want to backtest.  You'll also want to define any
    # parameters or values you're going to use.

    # In our example, we're looking at Neo in Ether.
    context.market = symbol(CONFIG.ASSET)
    context.asset = symbol(CONFIG.ASSET)
    context.base_price = None
    context.current_day = None

    context.RSI_OVERSOLD = 55
    context.RSI_OVERBOUGHT = 65
    context.CANDLE_SIZE = '5T'

    context.start_time = time.time()

    # context.set_commission(maker=0.1, taker=0.2)
    context.set_slippage(spread=0.0001)


def handle_data(context, data):
    # This handle_data function is where the real work is done.  Our data is
    # minute-level tick data, and each minute is called a frame.  This function
    # runs on each frame of the data.

    # We flag the first period of each day.
    # Since cryptocurrencies trade 24/7 the `before_trading_starts` handle
    # would only execute once. This method works with minute and daily
    # frequencies.

    today = data.current_dt.floor('1D')
    if today != context.current_day:
        context.traded_today = False
        context.current_day = today

    # We're computing the volume-weighted-average-price of the security
    # defined above, in the context.market variable.  For this example, we're
    # using three bars on the 15 min bars.

    # The frequency attribute determine the bar size. We use this convention
    # for the frequency alias:
    # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
    prices = data.history(
        context.market,
        fields='close',
        bar_count=50,
        frequency=context.CANDLE_SIZE
    )

    # Ta-lib calculates various technical indicator based on price and
    # volume arrays.

    # In this example, we are comp
    rsi = talib.RSI(prices.values, timeperiod=14)

    # We need a variable for the current price of the security to compare to
    # the average. Since we are requesting two fields, data.current()
    # returns a DataFrame with
    current = data.current(context.market, fields=['close', 'volume'])
    price = current['close']

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
        volume=current['volume'],
        price=price,
        price_change=price_change,
        rsi=rsi[-1],
        cash=cash
    )
    # We are trying to avoid over-trading by limiting our trades to
    # one per day.
    if context.traded_today:
        return

    # TODO: retest with open orders
    # Since we are using limit orders, some orders may not execute immediately
    # we wait until all orders are executed before considering more trades.
    orders = get_open_orders(context.market)
    if len(orders) > 0:
        log.info('exiting because orders are open: {}'.format(orders))
        return

    # Exit if we cannot trade
    if not data.can_trade(context.market):
        return

    # Another powerful built-in feature of the Catalyst backtester is the
    # portfolio object.  The portfolio object tracks your positions, cash,
    # cost basis of specific holdings, and more.  In this line, we calculate
    # how long or short our position is at this minute.
    pos_amount = context.portfolio.positions[context.market].amount

    if rsi[-1] <= context.RSI_OVERSOLD and pos_amount == 0:
        log.info(
            '{}: buying - price: {}, rsi: {}'.format(
                data.current_dt, price, rsi[-1]
            )
        )
        # Set a style for limit orders,
        limit_price = price * 1.005
        order_target_percent(
            context.market, 1, limit_price=limit_price
        )
        context.traded_today = True

    elif rsi[-1] >= context.RSI_OVERBOUGHT and pos_amount > 0:
        log.info(
            '{}: selling - price: {}, rsi: {}'.format(
                data.current_dt, price, rsi[-1]
            )
        )
        limit_price = price * 0.995
        order_target_percent(
            context.market, 0, limit_price=limit_price
        )
        context.traded_today = True

