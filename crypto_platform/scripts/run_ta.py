import click
import matplotlib.pyplot as plt
from logbook import Logger
from catalyst.api import get_open_orders, order, order_target_percent, cancel_order

from crypto_platform.utils import viz, algo
from crypto_platform.analysis.indicators import TAAnalysis


log = Logger('TA')

ta = TAAnalysis()


def sell(context):
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


def buy(context):
    # Buy when not holding and got buy signal
    # raise Exception
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
@click.option('--quick_enter/--no-quick-enter', '-e', default=False)
def run(indicators, quick_enter):
    """Runs a strategy based on specified TA indicators

        \b
        Example:
            ta -i macd -i bbands

        \b
        Available Indicators:
          - bbands
          - psar
          - macd
          - macdfix
          - obv
          - rsi
          - stoch
    """
    click.secho('Executing using indicators:\n{}'.format(indicators), fg='white')

    def initialize(context):
        algo.initialze_from_config(context)
        context.i = 0
        ta.track_indicators(list(indicators))

    def handle_data(context, data):
        algo.record_data(context, data)
        ta.calculate(context, data)
        ta.record()

        if context.i == 0 and quick_enter:
            buy(context)
            context.i += 1

        # Exit if we cannot trade
        if not data.can_trade(context.market):
            return

        for i in get_open_orders(context.asset):
            log.info('Canceling order')
            cancel_order(i)

        if ta.signals_buy:
            buy(context)
        elif ta.signals_sell:
            sell(context)
        else:
            log.info('No Trading Opportunity')

        if len(context.errors) > 0:
            log.info('the errors:\n{}'.format(context.errors))

    def analyze(context, results):
        pos = viz.get_start_geo(len(indicators) + 2)
        viz.plot_percent_return(results, pos=pos)
        viz.plot_benchmark(results, pos=pos)
        plt.legend()
        pos += 1
        for i in ta.active_indicators:
            i.plot(results, pos)
            pos += 1

        viz.plot_buy_sells(results, pos=pos)

    algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
