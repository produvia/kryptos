from catalyst.api import order_target_percent, record, symbol, set_benchmark
from logbook import Logger

CONFIG = None
NAMESPACE = "pugilist"
log = Logger(NAMESPACE)


def initialize(context):
    context.is_first_time = True
    context.INVEST_RATIO = .5


def trade_logic(context, data):

    # Define base price and make initial trades to achieve target investment

    # ratio of 0.5

    if context.is_first_time:
        order_target_percent(context.asset, 0.5)

        context.base_price = data.current(context.asset, "price")
        context.first_price = data.current(context.asset, "price")
        context.is_first_time = False

    # Retrieve current asset price from pricing data
    price = data.current(context.asset, "price")
    Asset_cumulative_return = (price / context.first_price - 1) * 100
    Portfolio_cumulative_return = (
        context.portfolio.portfolio_value / context.portfolio.starting_cash - 1
    ) * 100

    # Trading logic: rebalance to a 0.5 investment ratio every time the price
    # of the asset doubles or decreases to half the initial price
    if price > context.base_price * 1.1:
        order_target_percent(context.asset, 0.5)
        context.base_price = data.current(context.asset, "price")

    elif price < context.base_price / 1.1:
        order_target_percent(context.asset, 0.5)
        context.base_price = data.current(context.asset, "price")

    price = data.current(context.asset, "price")

    # Save values for later inspection
    record(
        price=price,
        base_price=context.base_price,
        cash=context.portfolio.cash,
        leverage=context.account.leverage,
        Portfolio_cumulative_return=Portfolio_cumulative_return,
        Asset_cumulative_return=Asset_cumulative_return,
    )
