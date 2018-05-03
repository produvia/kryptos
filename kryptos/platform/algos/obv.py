# http://traderhq.com/trading-indicators/understanding-on-balance-volume-and-how-to-use-it/
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.api import order, order_target_percent, get_open_orders


NAMESPACE = "obv"
log = Logger(NAMESPACE)


def initialize(context):
    log.info("Starting TALib Simple Example")

    # context.ORDER_SIZE = 10
    # context.SLIPPAGE_ALLOWED = 0.1

    # Bars to look at per iteration should be bigger than SMA_SLOW
    # context.BARS = 365

    context.swallow_errors = True
    context.errors = []


def trade_logic(context, data):
    log.info("handling bar {}".format(data.current_dt))
    try:
        perform_ta(context, data)
    except Exception as e:
        log.warn("aborting the bar on error {}".format(e))
        context.errors.append(e)
        log.error(e)
    # raise e

    log.info(
        "completed bar {}, total execution errors {}".format(data.current_dt, len(context.errors))
    )

    if len(context.errors) > 0:
        log.info("the errors:\n{}".format(context.errors))


def perform_ta(context, data):
    # Get price, open, high, low, close
    prices = data.history(
        context.asset, bar_count=context.BARS, fields=["price", "close", "volume"], frequency="1d"
    )

    # Create a analysis data frame
    analysis = pd.DataFrame(index=prices.index)

    # store prev obv before setting new obv val

    analysis["obv"] = ta.OBV(prices.close.as_matrix(), prices.volume.as_matrix())

    # Save the prices and analysis to send to analyze
    context.prices = prices
    context.analysis = analysis
    context.price = data.current(context.asset, "price")

    # Since we are using limit orders, some orders may not execute immediately
    # we wait until all orders are executed before considering more trades.
    orders = get_open_orders(context.asset)
    if len(orders) > 0:
        return

    # Exit if we cannot trade
    if not data.can_trade(context.asset):
        return

    makeOrders(context, analysis)

    # Log the values of this bar
    logAnalysis(analysis)


def makeOrders(context, analysis):
    if context.asset in context.portfolio.positions:

        # Current position
        position = context.portfolio.positions[context.asset]

        if position == 0:
            log.info("Position Zero")
            return

        # Cost Basis
        cost_basis = position.cost_basis

        log.info(
            "Holdings: {amount} @ {cost_basis}".format(
                amount=position.amount, cost_basis=cost_basis
            )
        )

        # Sell when holding and got sell singnal
        if isSell(context, analysis):
            profit = (context.price * position.amount) - (cost_basis * position.amount)
            order_target_percent(
                asset=context.asset,
                target=0,
                limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED),
            )
            log.info(
                "Sold {amount} @ {price} Profit: {profit}".format(
                    amount=position.amount, price=context.price, profit=profit
                )
            )
        else:
            log.info("no buy or sell opportunity found")
    else:
        # Buy when not holding and got buy signal
        if isBuy(context, analysis):
            if context.portfolio.cash < context.price * context.ORDER_SIZE:
                log.warn(
                    "Skipping signaled buy due to cash amount: {} < {}".format(
                        context.portfolio.cash, (context.price * context.ORDER_SIZE)
                    )
                )
                return
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED),
            )
            log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )


def isBuy(context, analysis):
    # Bullish OBV
    latest = analysis["obv"][analysis["obv"].index[-1]]
    prev = analysis["obv"][analysis["obv"].index[-2]]

    if latest > prev:
        log.warn("Sending Buy Signal")
        return True

    return False


def isSell(context, analysis):
    # Bearish OBV
    latest = analysis["obv"][analysis["obv"].index[-1]]
    prev = analysis["obv"][analysis["obv"].index[-2]]

    if latest < prev:
        log.warn("Sending Sell Signal")
        return True

    return False


def logAnalysis(analysis):
    # Log only the last value in the array
    log.info("- obv:          {:.2f}".format(get_last(analysis, "obv")))


def get_last(arr, name):
    return arr[name][arr[name].index[-1]]
