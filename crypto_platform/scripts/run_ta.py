from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol, get_open_orders, order, order_target_percent, cancel_order
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from crypto_platform.utils import load, outputs, viz
from crypto_platform.analysis.indicators import TAAnalysis
from crypto_platform.config import CONFIG
from logbook import Logger

import click

log = Logger('Comparison')


def record_data(context, data):
    # Let's keep the price of our asset in a more handy variable
    price = data.current(context.asset, 'price')

    # Save values for later inspection
    record(price=price, cash=context.portfolio.cash)


def perform_ta(context, data, ta_data, indicator):
    ta_data.update(context, data)

    ta_ind = getattr(ta_data, indicator)

    if ta_ind.is_bullish:
        signal_buy(context)

    elif ta_ind.is_bearish:
        signal_sell(context)

    else:
        log.info('no buy or sell opportunity found')


def signal_sell(context):
    # Current position
    if context.asset not in context.portfolio.positions:
        return
    position = context.portfolio.positions.get(context.asset)
    if position == 0:
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


def signal_buy(context):
    # Buy when not holding and got buy signal

    if context.asset not in context.portfolio.positions:
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


@click.command()
@click.option('--indicators', '-i', multiple=True)
def run(indicators):
    click.secho('Executing using indicators:\n{}'.format(indicators), fg='white')

    def initialize(context):

        context.ORDER_SIZE = 10
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365

        context.swallow_errors = True
        context.errors = []

        context.ASSET_NAME = CONFIG.ASSET
        context.asset = symbol(context.ASSET_NAME)
        context.market = symbol(CONFIG.ASSET)

        set_benchmark(context.asset)

    def handle_data(context, data):
        record_data(context, data)

        # Get price, open, high, low, close
        prices = data.history(
            context.asset,
            bar_count=context.BARS,
            fields=['price', 'open', 'high', 'low', 'close'],
            frequency='1d')

        # Save the prices and analysis to send to analyze
        context.prices = prices
        context.price = data.current(context.asset, 'price')
        log.info('handling bar {}'.format(data.current_dt))

        # Exit if we cannot trade
        if not data.can_trade(context.market):
            return

        for i in get_open_orders(context.asset):
            cancel_order(i)

        ta_data = TAAnalysis()

        for i in indicators:

            try:
                perform_ta(context, data, ta_data, indicator=i)
            except Exception as e:
                log.error('Failed to perform {} analysis'.format(i))
                log.warn('aborting the bar on error {}'.format(e))
                context.errors.append(e)
                raise e

        log.info('completed bar {}, total execution errors {}'.format(
            data.current_dt,
            len(context.errors)
        ))

        if len(context.errors) > 0:
            log.info('the errors:\n{}'.format(context.errors))

    def analyze(context, results):
        # pos = viz.get_start_geo(len(CONFIG.METRICS) + 1)
        viz.plot_percent_return(results)
        viz.plot_benchmark(results)

        viz.add_legend()
        viz.show_plot()

    try:
        run_algorithm(
            capital_base=CONFIG.CAPITAL_BASE,
            data_frequency=CONFIG.DATA_FREQUENCY,
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name=CONFIG.BUY_EXCHANGE,
            # algo_namespace=algo.NAMESPACE,
            base_currency=CONFIG.BASE_CURRENCY,
            start=CONFIG.START,
            end=CONFIG.END,
            # output=outputs.get_output_file('custom', CONFIG) + '.p'
        )
    except PricingDataNotLoadedError:
        log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)
        # log.info('Run completed for {}'.format(algo.NAMESPACE))
        # run(algos, metrics)
        # break


if __name__ == '__main__':
    run()
