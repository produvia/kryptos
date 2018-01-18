# From catalyst examples

from datetime import timedelta

import pandas as pd
import numpy as np
import talib
from logbook import Logger

from catalyst.api import (
    order,
    record,
    get_open_orders,
)
from catalyst.utils.run_algo import run_algorithm

CONFIG = None
NAMESPACE = 'rsi'
log = Logger(NAMESPACE)


def initialize(context):
    log.info('initializing algo')
    context.base_price = None

    context.MAX_HOLDINGS = 0.2
    context.RSI_OVERSOLD = 30
    context.RSI_OVERSOLD_BBANDS = 45
    context.RSI_OVERBOUGHT_BBANDS = 55
    context.SLIPPAGE_ALLOWED = 0.03

    context.TARGET = 0.15
    context.STOP_LOSS = 0.1
    context.STOP = 0.03
    context.position = None

    context.last_bar = None

    context.errors = []
    pass


def _handle_buy_sell_decision(context, data, signal, price):
    orders = get_open_orders(context.asset)
    if len(orders) > 0:
        log.info('skipping bar until all open orders execute')
        return

    positions = context.portfolio.positions
    if context.position is None and context.asset in positions:
        position = positions[context.asset]
        context.position = dict(
            cost_basis=position['cost_basis'],
            amount=position['amount'],
            stop=None
        )

    # action = None
    if context.position is not None:
        cost_basis = context.position['cost_basis']
        amount = context.position['amount']
        log.info(
            'found {amount} positions with cost basis {cost_basis}'.format(
                amount=amount,
                cost_basis=cost_basis
            )
        )
        stop = context.position['stop']

        target = cost_basis * (1 + context.TARGET)
        if price >= target:
            context.position['cost_basis'] = price
            context.position['stop'] = context.STOP

        stop_target = context.STOP_LOSS if stop is None else context.STOP
        if price < cost_basis * (1 - stop_target):
            log.info('executing stop loss')
            order(
                asset=context.asset,
                amount=-amount,
                limit_price=price * (1 - context.SLIPPAGE_ALLOWED),
            )
            # action = 0
            context.position = None

    else:
        if signal == 'long':
            log.info('opening position')
            buy_amount = context.MAX_HOLDINGS / price
            order(
                asset=context.asset,
                amount=buy_amount,
                limit_price=price * (1 + context.SLIPPAGE_ALLOWED),
            )
            context.position = dict(
                cost_basis=price,
                amount=buy_amount,
                stop=None
            )
            # action = 0


def _handle_data_rsi_only(context, data):
    price = data.current(context.asset, 'close')
    log.info('got price {price}'.format(price=price))

    if price is np.nan:
        log.warn('no pricing data')
        return

    if context.base_price is None:
        context.base_price = price

    try:
        prices = data.history(
            context.asset,
            fields='price',
            bar_count=20,
            frequency='30T'
        )
    except Exception as e:
        log.warn('historical data not available: '.format(e))
        return

    rsi = talib.RSI(prices.values, timeperiod=16)[-1]
    log.info('got rsi {}'.format(rsi))

    signal = None
    if rsi < context.RSI_OVERSOLD:
        signal = 'long'

    # Making sure that the price is still current
    price = data.current(context.asset, 'close')
    cash = context.portfolio.cash
    log.info(
        'base currency available: {cash}, cap: {cap}'.format(
            cash=cash,
            cap=context.MAX_HOLDINGS
        )
    )
    volume = data.current(context.asset, 'volume')
    price_change = (price - context.base_price) / context.base_price
    record(
        price=price,
        price_change=price_change,
        rsi=rsi,
        volume=volume,
        cash=cash,
        starting_cash=context.portfolio.starting_cash,
        leverage=context.account.leverage,
    )

    _handle_buy_sell_decision(context, data, signal, price)


def handle_data(context, data):
    dt = data.current_dt

    if context.last_bar is None or (
            context.last_bar + timedelta(minutes=15)) <= dt:
        context.last_bar = dt
    else:
        return

    log.info('BAR {}'.format(dt))
    try:
        _handle_data_rsi_only(context, data)
    except Exception as e:
        log.warn('aborting the bar on error {}'.format(e))
        context.errors.append(e)

    if len(context.errors) > 0:
        log.info('the errors:\n{}'.format(context.errors))





if __name__ == '__main__':
    # Backtest
    run_algorithm(
        capital_base=0.5,
        data_frequency='minute',
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name='poloniex',
        algo_namespace=algo_namespace,
        base_currency='btc',
        start=pd.to_datetime('2017-9-1', utc=True),
        end=pd.to_datetime('2017-10-1', utc=True),
    )
