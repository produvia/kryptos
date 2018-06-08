from kryptos.platform.strategy import Strategy
from kryptos.platform.strategy.indicators import technical
from catalyst.api import order_target_value, record

import logbook

log = logbook.Logger("BUY_AND_HODL")
log.level = logbook.INFO


strat = Strategy("BUY_AND_HODL", data_frequency="daily")


@strat.init
def init(context):
    log.info("Algo is being initialzed, setting up context")
    context.TARGET_HODL_RATIO = 0.8
    context.RESERVE_RATIO = 1.0 - context.TARGET_HODL_RATIO

    context.starting_cash = context.portfolio.starting_cash
    context.target_hodl_value = context.TARGET_HODL_RATIO * context.starting_cash
    context.reserve_value = context.RESERVE_RATIO * context.starting_cash

    context.is_buying = True
    context.i = 0


@strat.handle_data
def handle_data(context, data):
    context.i += 1
    if context.i == 1:
        order_target_value(context.asset, context.target_hodl_value, limit_price=context.price * 1.1)

    # Stop buying after passing the reserve threshold
    context.cash = context.portfolio.cash
    if context.cash <= context.reserve_value:
        context.is_buying = False

    context.price = data.current(context.asset, "price")


@strat.signal_buy
def signal_buy(context, data):
    return context.is_buying and context.cash > context.price


@strat.buy_order
def buy(context):
    order_target_value(context.asset, context.target_hodl_value, limit_price=context.price * 1.1)


@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info("Ending cash: ${}".format(ending_cash))
    log.info("Completed for {} trading periods".format(context.i))


if __name__ == "__main__":
    log.info("Strategy Schema:\n{}".format(strat.serialize()))
    strat.run()
