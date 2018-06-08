from kryptos.platform.strategy import Strategy
from kryptos.platform.strategy.indicators import technical
from catalyst.api import order_target_percent, record

import logbook

log = logbook.Logger("BEAR_MARKET")
log.level = logbook.INFO


strat = Strategy("BEAR_MARKET", data_frequency="daily")


@strat.init
def init(context):
    log.info("Algo is being initialzed, setting up context")
    context.i = 0
    context.IS_MARKET_BEAR = False


@strat.handle_data
def handle_data(context, data):
    log.debug("Processing new trading step")
    context.i += 1

    # Get price history for the last two months. Find peak, bottom, and last
    # prices for the period
    price_history = data.history(context.asset, fields="price", bar_count=60, frequency="1d")
    context.peak = price_history.max()
    context.bottom = price_history.min()
    context.price = price_history.ix[-1]

    Portfolio_cumulative_return = (
        context.portfolio.portfolio_value / context.portfolio.starting_cash - 1
    ) * 100

    record(
        peak=context.peak,
        bottom=context.bottom,
        cash=context.portfolio.cash,
        leverage=context.account.leverage,
        Portfolio_cumulative_return=Portfolio_cumulative_return,
    )


# Trading logic:
# If current price is more than 20% lower than highest-closing price over a
# 2-month period, market enters Bear territory and algorithm sells all
# asset and holds only cash. Market exits bear market when prices are at
# least 20% higher than lowest-closing price over a 2-month period. In this
# case, algorithm invests 90% of portfolio in the asset.
@strat.signal_sell
def enter_bear(context, data):
    return context.price < 0.75 * context.peak


@strat.signal_buy
def exit_bear(context, data):
    return context.price > 1.2 * context.bottom


@strat.sell_order
def sell(context):
    order_target_percent(context.asset, 0.3)


@strat.buy_order
def buy(context):
    order_target_percent(context.asset, 0.75)


@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info("Ending cash: ${}".format(ending_cash))
    log.info("Completed for {} trading periods".format(context.i))


if __name__ == "__main__":
    log.info("Strategy Schema:\n{}".format(strat.serialize()))
    strat.run()
