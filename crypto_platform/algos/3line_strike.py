# The bullish three line strike reversal pattern carves out three black candles within a downtrend.
# Each bar posts a lower low and closes near the intrabar low.
# The fourth bar opens even lower but reverses in a wide - range outside bar that closes above the high of the first candle in the series.
# The opening print also marks the low of the fourth bar.
# According to Bulkowski, this reversal predicts higher prices with an 84 % accuracy rate.
# https://www.investopedia.com/articles/active-trading/092315/5-most-powerful-candlestick-patterns.asp

import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.api import order, order_target_percent


NAMESPACE = "3line_strike"
log = Logger(NAMESPACE)


def initialize(context):
    log.info("Starting TALib Simple Example")

    context.ORDER_SIZE = 10
    context.SLIPPAGE_ALLOWED = 0.05

    context.swallow_errors = True
    context.errors = []

    # Bars to look at per iteration should be bigger than SMA_SLOW
    context.BARS = 365
    context.COUNT = 0

    # Technical Analysis Settings
    context.SMA_FAST = 50
    context.SMA_SLOW = 100

    pass


def perform_ta(context, data):
    # Get price, open, high, low, close
    prices = data.history(
        context.asset,
        bar_count=context.BARS,
        fields=["open", "high", "low", "close"],
        frequency="1d",
    )

    # Create a analysis data frame
    analysis = pd.DataFrame(index=prices.index)

    analysis["3line_strike"] = ta.CDL3LINESTRIKE(
        prices.open.as_matrix(),
        prices.high.as_matrix(),
        prices.low.as_matrix(),
        prices.close.as_matrix(),
    )

    # Save the prices and analysis to send to analyze
    context.prices = prices
    context.analysis = analysis
    context.price = data.current(context.asset, "price")

    makeOrders(context, analysis)

    # Log the values of this bar
    logAnalysis(analysis)


def trade_logic(context, data):
    log.info("handling bar {}".format(data.current_dt))
    try:
        perform_ta(context, data)
    except Exception as e:
        log.warn("aborting the bar on error {}".format(e))
        context.errors.append(e)

    log.info(
        "completed bar {}, total execution errors {}".format(data.current_dt, len(context.errors))
    )

    if len(context.errors) > 0:
        log.info("the errors:\n{}".format(context.errors))


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
                limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED)
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
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED)
            )
            log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )


def isBuy(context, analysis):
    if getLast(analysis, "3line_strike") == 100:
        return True

    return False


def isSell(context, analysis):
    if getLast(analysis, "3line_strike") == -100:
        return True

    return False


def logAnalysis(analysis):
    # Log only the last value in the array
    log.info("- 3line_strike:          {:.2f}".format(getLast(analysis, "3line_strike")))


def getLast(arr, name):
    return arr[name][arr[name].index[-1]]
