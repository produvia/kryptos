from kryptos.strategy import Strategy
from kryptos.strategy.indicators import technical
from catalyst.api import order_target_percent, order, record

import logbook

log = logbook.Logger("BUY_LOW_SELL_HIGH")
log.level = logbook.INFO


strat = Strategy("BUY_LOW_SELL_HIGH", data_frequency="daily")

rsi = technical.get_indicator("RSI")
rsi.update_param("timeperiod", 14)

strat.add_market_indicator(rsi)


@strat.init
def init(context):
    context.TARGET_POSITIONS = 30
    context.PROFIT_TARGET = 0.1
    context.SLIPPAGE_ALLOWED = 0.02
    context.cost_basis = None
    context.buy_increment = None
    context.i = 0


@strat.handle_data
def handle_data(context, data):
    context.i += 1

    context.price = data.current(context.asset, "price")
    context.position = context.portfolio.positions.get(context.asset)

    rsi = strat.indicator("RSI").outputs["RSI"][-1]

    # Buying more when RSI is low, this should lower our cost basis
    if rsi <= 30:
        context.buy_increment = 1
    elif rsi <= 40:
        context.buy_increment = 0.5
    elif rsi <= 70:
        context.buy_increment = 0.2
    else:
        context.buy_increment = 0.1

    if context.position:
        context.cost_basis = context.position.cost_basis

        log.info(
            "found {amount} positions with cost basis {cost_basis}".format(
                amount=context.position.amount, cost_basis=context.cost_basis
            )
        )

        if context.position.amount >= context.TARGET_POSITIONS:
            log.info("reached positions target: {}".format(context.position.amount))
            return


@strat.signal_buy(override=False)
def signal_buy(context, data):
    if context.cost_basis:
        return context.price < context.cost_basis


@strat.signal_sell(override=False)
def signal_sell(context, data):
    if not context.position:
        return False
    if context.cost_basis and context.price < context.cost_basis:
        return False

    return (
        context.position.amount > 0
        and context.price > context.cost_basis * (1 + context.PROFIT_TARGET)
    )


@strat.buy_order
def buy(context):
    if context.buy_increment is None:
        rsi = strat.indicator("RSI")
        log.info("the rsi is too high to consider buying {}".format(strat.rsi.outputs[-1]))
        return

    if context.price * context.buy_increment > context.portfolio.cash:
        log.info("not enough base currency to consider buying")
        return

    log.info(
        "buying position cheaper than cost basis {} < {}".format(context.price, context.cost_basis)
    )
    order(
        asset=context.asset,
        amount=context.buy_increment,
        limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED),
    )


@strat.sell_order
def sell(context):
    profit = (context.price * context.position.amount) - (
        context.cost_basis * context.position.amount
    )
    log.info("closing position, taking profit: {}".format(profit))
    order_target_percent(
        asset=context.asset, target=0, limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED)
    )


@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info("Ending cash: ${}".format(ending_cash))
    log.info("Completed for {} trading periods".format(context.i))


if __name__ == "__main__":
    log.info("Strategy Schema:\n{}".format(strat.serialize()))
    strat.run()
