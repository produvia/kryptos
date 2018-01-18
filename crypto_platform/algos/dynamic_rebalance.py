from catalyst.api import order_target_percent, record, symbol, cancel_order, get_open_orders
from logbook import Logger

CONFIG = None
NAMESPACE = 'dynamic_rebalance'
log = Logger(NAMESPACE)

def initialize(context):
    # For all trading pairs in the poloniex bundle, the default denomination
    # currently supported by Catalyst is 1/1000th of a full coin. Use this
    # constant to scale the price of up to that of a full coin if desired.
    # context.TICK_SIZE = 1.0
    pass


def handle_data(context, data):

    # Cancel any outstanding orders
    orders = get_open_orders(context.asset) or []
    for order in orders:
        cancel_order(order)

    # Define base price and make initial trades to achieve target investment ratio of 0.5
    order_target_percent(
        context.asset,
        0.5,
    )

    # Retrieve current asset price from pricing data
    price = data.current(context.asset, 'price')

    # Compute portfolio cumulative return
    Portfolio_cumulative_return = (context.portfolio.portfolio_value / context.portfolio.starting_cash - 1) * 100
    # Save values for later inspection
    record(price=price,
           cash=context.portfolio.cash,
           leverage=context.account.leverage,
           Portfolio_cumulative_return=Portfolio_cumulative_return
           )

