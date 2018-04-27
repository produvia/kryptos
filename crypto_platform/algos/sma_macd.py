# From catalyst examples

# Run Command
# catalyst run --start 2017-1-1 --end 2017-11-1 -o talib_simple.pickle \
#   -f talib_simple.py -x poloniex
#
# Description
# Simple TALib Example showing how to use various indicators
# in you strategy. Based loosly on
# https://github.com/mellertson/talib-macd-example/blob/master/talib-macd-matplotlib-example.py

import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.api import order, order_target_percent


NAMESPACE = "sma_macd"
log = Logger(NAMESPACE)


def initialize(context):
    log.info("Starting TALib Simple Example")

    # context.ORDER_SIZE = 10
    # context.SLIPPAGE_ALLOWED = 0.05

    context.swallow_errors = True
    context.errors = []

    # Bars to look at per iteration should be bigger than SMA_SLOW
    # context.BARS = 365
    context.COUNT = 0

    # Technical Analysis Settings
    # context.SMA_FAST = 50
    # context.SMA_SLOW = 100
    # context.MACD_FAST = 12
    # context.MACD_SLOW = 26
    # context.MACD_SIGNAL = 9

    pass


def perform_ta(context, data):
    # Get price, open, high, low, close
    prices = data.history(
        context.asset,
        bar_count=context.BARS,
        fields=["price", "open", "high", "low", "close"],
        frequency="1d",
    )

    # Create a analysis data frame
    analysis = pd.DataFrame(index=prices.index)

    # SMA FAST
    analysis["sma_f"] = ta.SMA(prices.close.as_matrix(), context.SMA_FAST)
    log.info(analysis["sma_f"].values)

    # SMA SLOW
    analysis["sma_s"] = ta.SMA(prices.close.as_matrix(), context.SMA_SLOW)

    # MACD, MACD Signal, MACD Histogram
    analysis["macd"], analysis["macdSignal"], analysis["macdHist"] = ta.MACD(
        prices.close.as_matrix(),
        fastperiod=context.MACD_FAST,
        slowperiod=context.MACD_SLOW,
        signalperiod=context.MACD_SIGNAL,
    )

    # SMA FAST over SLOW Crossover
    analysis["sma_test"] = np.where(analysis.sma_f > analysis.sma_s, 1, 0)

    # MACD over Signal Crossover
    analysis["macd_test"] = np.where((analysis.macd > analysis.macdSignal), 1, 0)

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
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED)
            )
            log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )


def isBuy(context, analysis):
    # Bullish SMA Crossover
    if getLast(analysis, "sma_test") == 1:
        # Bullish MACD
        if getLast(analysis, "macd_test") == 1:
            return True

    return False


def isSell(context, analysis):
    # Bearish SMA Crossover
    if getLast(analysis, "sma_test") == 0:
        # Bearish MACD
        if getLast(analysis, "macd_test") == 0:
            return True

    return False


def logAnalysis(analysis):
    # Log only the last value in the array
    log.info("- sma_f:          {:.2f}".format(getLast(analysis, "sma_f")))
    log.info("- sma_s:          {:.2f}".format(getLast(analysis, "sma_s")))

    # log.info('- sma_r:          {:.2f}'.format(getLast(analysis, 'sma_r')))

    log.info("- macd:           {:.2f}".format(getLast(analysis, "macd")))
    log.info("- macdSignal:     {:.2f}".format(getLast(analysis, "macdSignal")))
    log.info("- macdHist:       {:.2f}".format(getLast(analysis, "macdHist")))

    log.info("- sma_test:       {}".format(getLast(analysis, "sma_test")))
    log.info("- macd_test:      {}".format(getLast(analysis, "macd_test")))


def getLast(arr, name):
    return arr[name][arr[name].index[-1]]
