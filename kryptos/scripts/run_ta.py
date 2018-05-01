import click

from logbook import Logger
from catalyst.api import order, order_target_percent

from kryptos.platform.strategy import Strategy


log = Logger("TA")


@click.command()
@click.option("--indicators", "-i", multiple=True)
@click.option("--quick_enter/--no-quick-enter", "-e", default=False)
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
    click.secho("Executing using indicators:\n{}".format(indicators), fg="white")

    strat = Strategy()

    for i in indicators:
        strat.add_market_indicator(i.upper())

    @strat.init
    def initialize(context):
        context.i = 0

    @strat.handle_data
    def handle_data(context, data):
        if context.i == 0 and quick_enter:
            log.info("Quick Entering market")
            strat.make_buy(context)
            context.i += 1

    @strat.sell_order
    def sell(context):
        if context.asset not in context.portfolio.positions:
            return

        position = context.portfolio.positions.get(context.asset)
        if position == 0:
            log.info("Position Zero")
            return

        cost_basis = position.cost_basis
        log.info(
            "Holdings: {amount} @ {cost_basis}".format(
                amount=position.amount, cost_basis=cost_basis
            )
        )

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

    @strat.buy_order
    def buy(context):
        log.info("Making Buy Order")
        if context.portfolio.cash < context.price * context.ORDER_SIZE:
            log.warn(
                "Skipping signaled buy due to cash amount: {} < {}".format(
                    context.portfolio.cash, (context.price * context.ORDER_SIZE)
                )
            )

        if context.asset not in context.portfolio.positions:
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED),
            )
            log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )

    strat.run()


if __name__ == "__main__":
    run()
