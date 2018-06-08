import talib as ta
from kryptos.platform.strategy import Strategy
from kryptos.platform.strategy.indicators import technical
from catalyst.api import order_target_percent, order, record, get_open_orders

import logbook


strat = Strategy("BBANDS_PSAR", data_frequency="daily")

strat.load_from_json('bbands_psar.json')

log = logbook.Logger(strat.name)

@strat.init
def initialize(context):


    context.swallow_errors = True
    context.errors = []

    # Bars to look at per iteration should be bigger than SMA_SLOW
    # context.BARS = 365

    context.ORDER_SIZE = 0.5
    # context.SLIPPAGE_ALLOWED =


@strat.handle_data
def trade_logic(context, data):
    log.info("handling bar {}".format(data.current_dt))

    context.price = data.current(context.asset, "price")

    today = data.current_dt.floor("1D")
    if today != context.current_day:
        context.traded_today = False
        context.current_day = today


@strat.buy_order
def buy(context):

    position = context.portfolio.positions[context.asset]

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

@strat.sell_order
def sell(context):
    position = context.portfolio.positions[context.asset]

    if position == 0:
        log.info("Position Zero")
        return
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


@strat.signal_buy(override=True)
def is_buy(context, analysis):
    log.info('{}   {}'.format(strat.indicator('BBANDS').outputs['upperband'][-1], context.price))
    if context.price > strat.indicator('BBANDS').outputs['upperband'][-1]:
        return True


@strat.signal_sell(override=True)
def isSell(context, analysis):
    if context.price <  strat.indicator('SAR').outputs['SAR'][-1]:
        log.info("Closing position due to PSAR")
        return True
