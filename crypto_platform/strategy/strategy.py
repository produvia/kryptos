from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record, order, order_target_percent
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError
from logbook import Logger

from crypto_platform.config import CONFIG
from crypto_platform.utils import load
from crypto_platform.analysis import indicators

log = Logger('Strategy')


class Strategy(object):

    def __init__(self):
        super(Strategy, self).__init__()
        self._indicators = []

    def setup_context(self, context, config=None):
        """Stores config options catalyst's context object"""
        if config is None:
            config = CONFIG
        context.asset = symbol(CONFIG.ASSET)
        context.market = symbol(CONFIG.ASSET)
        set_benchmark(context.asset)
        context.ORDER_SIZE = 10
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365
        context.errors = []
        for k, v in CONFIG.__dict__.items():
            if '__' not in k:
                setattr(context, k, v)

    def add_indicator(self, indicator, priority=0, **kw):
        ind_class = getattr(indicators, indicator)
        indicator = ind_class(**kw)
        self._indicators.insert(indicator, priority)

    def process_data(self, context, data):
        price = data.current(context.asset, 'price')
        cash = context.portfolio.cash
        record(price=price, cash=cash)
        # Get price, open, high, low, close
        context.prices = data.history(
            context.asset,
            bar_count=context.BARS,
            fields=['price', 'open', 'high', 'low', 'close'],
            frequency='1d',
        )
        for i in self._indicators:
            i.calculate(context, data)
            i.record()
        self.execute_trades(context, data)

    def weigh_signals(self, context, data):
        raise NotImplementedError

    def place_buy(self, context, size=None, price=None, slippage=None):
        if context.asset not in context.portfolio.positions:
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED),
            )
            log.info(
                'Bought {amount} @ {price}'.format(
                    amount=context.ORDER_SIZE, price=context.price
                )
            )

    def place_sell(self, context, size=None, price=None, slippage=None):
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
                amount=position.amount, cost_basis=cost_basis
            )
        )
        # Sell when holding and got sell singnal
        profit = (context.price * position.amount) - (cost_basis * position.amount)
        order_target_percent(
            asset=context.asset,
            target=0,
            limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED),
        )
        log.info(
            'Sold {amount} @ {price} Profit: {profit}'.format(
                amount=position.amount, price=context.price, profit=profit
            )
        )

    # Save the prices and analysis to send to analyze
    def run(self, initialize, handle_data, analyze):
        try:
            run_algorithm(
                capital_base=CONFIG.CAPITAL_BASE,
                data_frequency=CONFIG.DATA_FREQUENCY,
                initialize=initialize,
                handle_data=handle_data,
                analyze=analyze,
                exchange_name=CONFIG.BUY_EXCHANGE,
                base_currency=CONFIG.BASE_CURRENCY,
                start=CONFIG.START,
                end=CONFIG.END,
            )
        except PricingDataNotLoadedError:
            log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)
