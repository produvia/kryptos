# From catalyst examples

# For this example, we're going to write a simple momentum script.  When the
# stock goes up quickly, we're going to buy; when it goes down quickly, we're
# going to sell.  Hopefully we'll ride the waves.
import time

import talib
from kryptos.strategy import Strategy
from kryptos.strategy.indicators import technical
from catalyst.api import order_target_percent, order, record, get_open_orders, symbol

import logbook



strat = Strategy("MEAN_REVERSION", data_frequency="daily")

strat.load_from_json('mean_reversion.json')

log = logbook.Logger(strat.name)


# To run an algorithm in Catalyst, you need two functions: initialize and
# handle_data.

@strat.initialize
def initialize(context):
    # This initialize function sets any data or variables that you'll use in
    # your algorithm.  For instance, you'll want to define the trading pair (or
    # trading pairs) you want to backtest.  You'll also want to define any
    # parameters or values you're going to use.

    # In our example, we're looking at Neo in Ether.
    context.base_price = None
    context.current_day = None

    context.RSI_OVERSOLD = 55
    context.RSI_OVERBOUGHT = 65
    context.CANDLE_SIZE = "5T"

    context.start_time = time.time()

    # context.set_commission(maker=0.1, taker=0.2)
    context.set_slippage(spread=0.0001)

@strat.handle_data
def trade_logic(context, data):
    # If base_price is not set, we use the current value. This is the
    # price at the first bar which we reference to calculate price_change.
    if context.base_price is None:
        context.base_price = price

    price_change = (price - context.base_price) / context.base_price
    cash = context.portfolio.cash

    # Now that we've collected all current data for this frame, we use
    # the record() method to save it. This data will be available as
    # a parameter of the analyze() function for further analysis.


    @strat.signal_buy(override=True)
    def signal_buy(context, analyze):
    pos_amount = context.portfolio.positions[context.market].amount
    rsi = strat.indicator('RSI').outputs['RSI']
    return rsi[-1] <= context.RSI_OVERSOLD and pos_amount == 0

    @strat.signal_sell(override=True)
    def signal_sell(context, analyze):
    pos_amount = context.portfolio.positions[context.market].amount
    rsi = strat.indicator('RSI').outputs['RSI']
    return rsi[-1] >= context.RSI_OVERBOUGHT and pos_amount > 0


@strat.buy_order
def buy(context)
    # Set a style for limit orders,
    limit_price = price * 1.005
    order_target_percent(context.market, 1, limit_price=limit_price)
    context.traded_today = True

@strat.sell_order
def sell(context)
    log.info("{}: selling - price: {}, rsi: {}".format(data.current_dt, price, rsi[-1]))
    limit_price = price * 0.995
    order_target_percent(context.market, 0, limit_price=limit_price)
    context.traded_today = True
