import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.api import (
    order,
    order_target_percent,
    get_open_orders,
    cancel_order
)


NAMESPACE = 'bbands_psar'
log = Logger(NAMESPACE)


def initialize(context):
    log.info('Starting TALib Simple Example')

    context.ORDER_SIZE = 10
    context.SLIPPAGE_ALLOWED = 0.05

    context.swallow_errors = True
    context.errors = []

    # Bars to look at per iteration should be bigger than SMA_SLOW
    context.BARS = 365

    context.MATYPE = ta.MA_Type.T3
    context.SAR_ACCEL = 0.02
    context.SAR_MAX = 0.2


def close_open_orders(context, asset):
    orders = get_open_orders(asset)
    if orders:
        for order in orders:
            cancel_order(order)


def perform_ta(context, data):

    today = data.current_dt.floor('1D')
    if today != context.current_day:
        context.traded_today = False
        context.current_day = today

    # Get price, open, high, low, close
    prices = data.history(
        context.asset,
        bar_count=context.BARS,
        fields=['price', 'open', 'high', 'low', 'close'],
        frequency='1d')

    # Create a analysis data frame
    analysis = pd.DataFrame(index=prices.index)

    analysis['bb_upper'], analysis['bb_middle'], analysis['bb_lower'] = ta.BBANDS(
        prices.close.as_matrix(), matype=ta.MA_Type.T3)

    analysis['psar'] = ta.SAR(
        prices.high.as_matrix(),
        prices.low.as_matrix(),
        acceleration=context.SAR_ACCEL,
        maximum=context.SAR_MAX)

    # Save the prices and analysis to send to analyze
    context.prices = prices
    context.analysis = analysis

    # current price is the close price - used to comapre against psar
    context.price = data.current(context.asset, 'price')

    makeOrders(context, analysis)

    # # Log the values of this bar
    logAnalysis(analysis)


def trade_logic(context, data):
    log.info('handling bar {}'.format(data.current_dt))

    # Exit if we cannot trade
    if not data.can_trade(context.market):
        return

    for i in get_open_orders(context.asset):
        cancel_order(i)

    try:
        perform_ta(context, data)
    except Exception as e:
        log.warn('aborting the bar on error {}'.format(e))
        context.errors.append(e)
        raise e

    log.info('completed bar {}, total execution errors {}'.format(
        data.current_dt,
        len(context.errors)
    ))

    if len(context.errors) > 0:
        log.info('the errors:\n{}'.format(context.errors))


def makeOrders(context, analysis):

    if context.asset in context.portfolio.positions:

        # Current position
        position = context.portfolio.positions[context.asset]

        if (position == 0):
            log.info('Position Zero')
            return

        # Cost Basis
        cost_basis = position.cost_basis

        log.info(
            'Holdings: {amount} @ {cost_basis}'.format(
                amount=position.amount,
                cost_basis=cost_basis
            )
        )

        # Sell when holding and got sell singnal
        if isSell(context, analysis):
            profit = (context.price * position.amount) - (
                cost_basis * position.amount)
            order_target_percent(
                asset=context.asset,
                target=0,
                limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED),
            )
            log.info(
                'Sold {amount} @ {price} Profit: {profit}'.format(
                    amount=position.amount,
                    price=context.price,
                    profit=profit
                )
            )
        else:
            log.info('no buy or sell opportunity found')
    else:
        # Buy when not holding and got buy signal
        if isBuy(context, analysis):
            if context.portfolio.cash < context.price * context.ORDER_SIZE:
                log.warn('Skipping signaled buy due to cash amount: {} < {}'.format(
                    context.portfolio.cash, (context.price * context.ORDER_SIZE)))
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED)
            )
            log.info(
                'Bought {amount} @ {price}'.format(
                    amount=context.ORDER_SIZE,
                    price=context.price
                )
            )


def isBuy(context, analysis):
    if context.price > getLast(analysis, 'bb_upper'):
        return True

    return False


def isSell(context, analysis):
    if context.price < getLast(analysis, 'psar'):
        log.info('Closing position due to PSAR')
        return True

    # if context.price < getLast(analysis, 'bb_lower'):
    #     return True

    return False


def logAnalysis(analysis):
    # Log only the last value in the array
    log.info('- bb_upper:           {:.2f}'.format(getLast(analysis, 'bb_upper')))
    log.info('- bb_lower:           {:.2f}'.format(getLast(analysis, 'bb_lower')))


def getLast(arr, name):
    return arr[name][arr[name].index[-1]]
