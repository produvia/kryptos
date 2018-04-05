from catalyst.api import order_target_percent, record, symbol, cancel_order, get_open_orders
from logbook import Logger


NAMESPACE = 'dynamic_rebalance'
log = Logger(NAMESPACE)

def initialize(context):
    pass


def trade_logic(context, data):

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

