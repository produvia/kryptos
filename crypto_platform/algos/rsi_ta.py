# From catalyst examples

# Run Command
# catalyst run --start 2017-1-1 --end 2017-11-1 -o talib_simple.pickle \
#   -f talib_simple.py -x poloniex
#
# Description
# Simple TALib Example showing how to use various indicators
# in you strategy. Based loosly on
# https://github.com/mellertson/talib-macd-example/blob/master/talib-macd-matplotlib-example.py

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger
from matplotlib.dates import date2num
from matplotlib.finance import candlestick_ohlc

from catalyst.api import (
    order,
    order_target_percent,
)

NAMESPACE = 'rsi_ta'
log = Logger(NAMESPACE)


def initialize(context):
    log.info('Starting TALib Simple Example')

    context.ORDER_SIZE = 10
    context.SLIPPAGE_ALLOWED = 0.05

    context.swallow_errors = True
    context.errors = []

    # Bars to look at per iteration should be bigger than SMA_SLOW
    context.BARS = 365
    context.COUNT = 0

    # Technical Analysis Settings
    context.RSI_PERIOD = 14
    context.RSI_OVER_BOUGHT = 80
    context.RSI_OVER_SOLD = 20
    context.RSI_AVG_PERIOD = 15

    pass


def perform_ta(context, data):
    # Get price, open, high, low, close
    prices = data.history(
        context.asset,
        bar_count=context.BARS,
        fields=['price', 'open', 'high', 'low', 'close'],
        frequency='1d')

    # Create a analysis data frame
    analysis = pd.DataFrame(index=prices.index)

    # Relative Strength Index
    analysis['rsi'] = ta.RSI(prices.close.as_matrix(), context.RSI_PERIOD)
    # RSI SMA
    analysis['sma_r'] = ta.SMA(analysis.rsi.as_matrix(),
                               context.RSI_AVG_PERIOD)

    # RSI OVER BOUGHT & Decreasing
    analysis['rsi_over_bought'] = np.where(
        (analysis.rsi > context.RSI_OVER_BOUGHT) & (
            analysis.rsi < analysis.rsi.shift(1)), 1, 0)

    # RSI OVER SOLD & Increasing
    analysis['rsi_over_sold'] = np.where(
        (analysis.rsi < context.RSI_OVER_SOLD) & (
            analysis.rsi > analysis.rsi.shift(1)), 1, 0)

    # Save the prices and analysis to send to analyze
    context.prices = prices
    context.analysis = analysis
    context.price = data.current(context.asset, 'price')

    makeOrders(context, analysis)

    # Log the values of this bar
    logAnalysis(analysis)


def trade_logic(context, data):
    log.info('handling bar {}'.format(data.current_dt))
    try:
        perform_ta(context, data)
    except Exception as e:
        log.warn('aborting the bar on error {}'.format(e))
        context.errors.append(e)

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
    # Bullish RSI
    if(getLast(analysis, 'rsi_over_sold') == 1):
        return True

    return False


def isSell(context, analysis):
    # Bearish RSI
    if(getLast(analysis, 'rsi_over_bought') == 0):
        return True

    return False


def logAnalysis(analysis):
    # Log only the last value in the array
    log.info('- rsi:            {:.2f}'.format(getLast(analysis, 'rsi')))
    log.info('- rsi_over_bought:       {}'.format(
        getLast(analysis, 'rsi_over_bought')))
    log.info(
        '- rsi_over_sold:       {}'.format(getLast(analysis, 'rsi_over_sold')))


def getLast(arr, name):
    return arr[name][arr[name].index[-1]]
