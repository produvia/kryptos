from kryptos.platform.strategy import Strategy
from kryptos.platform.strategy.indicators import technical
from catalyst.api import order_target_percent, order, record, get_open_orders

import logbook

log = logbook.Logger("DUAL_MOVING_AVG")
log.level = logbook.INFO


strat = Strategy("DUAL_MOVING_AVG", data_frequency="daily")

#
# short_avg = technical.get_indicator('SMA')
# long_avg = technical.get_indicator('SMA')
#
# strat.add_market_indicator(short_avg)
# strat.add_market_indicator(long_avg)

strat.load_from_json('dual_moving_average.json')

@strat.init
def init(context):
    context.i = 0
    context.base_price = None


@strat.handle_data
def trade_logic(context, data):
    # define the windows for the moving averages
    short_window = 50
    long_window = 200

    # Skip as many bars as long_window to properly compute the average
    context.i += 1
    if context.i < long_window:
        return

    # Compute moving averages calling data.history() for each
    # moving average with the appropriate parameters. We choose to use
    # minute bars for this simulation -> freq="1m"
    # Returns a pandas dataframe.
    short_mavg = data.history(context.asset, "price", bar_count=short_window, frequency="1D").mean()
    long_mavg = data.history(context.asset, "price", bar_count=long_window, frequency="1D").mean()

    # Let's keep the price of our asset in a more handy variable
    price = data.current(context.asset, "price")

    # If base_price is not set, we use the current value. This is the
    # price at the first bar which we reference to calculate price_change.
    if context.base_price is None:
        context.base_price = price
    price_change = (price - context.base_price) / context.base_price

    # Save values for later inspection
    record(
        price=price,
        cash=context.portfolio.cash,
        price_change=price_change,
        short_mavg=short_mavg,
        long_mavg=long_mavg,
    )

    # Since we are using limit orders, some orders may not execute immediately
    # we wait until all orders are executed before considering more trades.
    orders = get_open_orders(context.asset)
    if len(orders) > 0:
        return

    # Exit if we cannot trade
    if not data.can_trade(context.asset):
        return

    # We check what's our position on our portfolio and trade accordingly
    pos_amount = context.portfolio.positions[context.asset].amount

    # Trading logic
    if short_mavg > long_mavg and pos_amount == 0:
        # we buy 100% of our portfolio for this asset
        order_target_percent(context.asset, 1)
    elif short_mavg < long_mavg and pos_amount > 0:
        # we sell all our positions for this asset
        order_target_percent(context.asset, 0)




# @strat.handle_data
# def handle_data(context, data):
#     context.i += 1
#
#     log.error('short: {}'.format(strat.indicator('SMA_SHORT').outputs['SMA_SHORT'][-1]))
#     log.error('long: {}\n\n'.format(strat.indicator('SMA_LONG').outputs['SMA_LONG'][-1]))
#
#
# @strat.signal_buy(override=True)
# def signal_buy(context, data):
#     # We check what's our position on our portfolio and trade accordingly
#     pos_amount = context.portfolio.positions[context.asset].amount
#     # import pdb; pdb.set_trace()
#
#     short_mavg = strat.indicator('SMA_SHORT').outputs['SMA_SHORT'][-1]
#     long_mavg = strat.indicator('SMA_LONG').outputs['SMA_LONG'][-1]
#
#     if long_mavg:
#         return short_mavg > long_mavg and pos_amount == 0
#
# @strat.signal_sell(override=True)
# def signal_sell(context, data):
#     pos_amount = context.portfolio.positions[context.asset].amount
#     short_mavg = strat.indicator('SMA_SHORT').outputs['SMA_SHORT'][-1]
#     long_mavg = strat.indicator('SMA_LONG').outputs['SMA_LONG'][-1]
#
#     if long_mavg:
#         return short_mavg < long_mavg and pos_amount > 0
#
# @strat.buy_order
# def buy(context):
#     order_target_percent(context.asset, 1)
#
#
# @strat.sell_order
# def sell(context):
#     order_target_percent(context.asset, 0)
#

@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info("Ending cash: ${}".format(ending_cash))
    log.info("Completed for {} trading periods".format(context.i))


if __name__ == "__main__":
    log.info("Strategy Schema:\n{}".format(strat.serialize()))
    strat.run()
