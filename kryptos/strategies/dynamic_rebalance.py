from kryptos.platform.strategy import Strategy
from kryptos.platform.strategy.indicators import technical
from catalyst.api import order_target_percent, order, record, get_open_orders

import logbook

log = logbook.Logger("DYNAMIC_REBALANCE")
log.level = logbook.INFO


strat = Strategy("DYNAMIC_REBALANCE", data_frequency="daily")


@strat.init
def initialize(context):
    context.i = 0
    context.base_price = None


@strat.handle_data
def trade_logic(context, data):

    # Cancel any outstanding orders
    orders = get_open_orders(context.asset) or []
    for order in orders:
        cancel_order(order)

    # Define base price and make initial trades to achieve target investment ratio of 0.5
    order_target_percent(context.asset, 0.5)

    # Retrieve current asset price from pricing data
    price = data.current(context.asset, "price")

    # Compute portfolio cumulative return
    Portfolio_cumulative_return = (
        context.portfolio.portfolio_value / context.portfolio.starting_cash - 1
    ) * 100
    # Save values for later inspection
    record(
        price=price,
        cash=context.portfolio.cash,
        leverage=context.account.leverage,
        Portfolio_cumulative_return=Portfolio_cumulative_return,
    )


@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info("Ending cash: ${}".format(ending_cash))
    log.info("Completed for {} trading periods".format(context.i))


if __name__ == "__main__":
    log.info("Strategy Schema:\n{}".format(strat.serialize()))
    strat.run()
