from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record, order, order_target_percent
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError
from logbook import Logger
import matplotlib.pyplot as plt

from crypto_platform.config import CONFIG
from crypto_platform.utils import load, viz
from crypto_platform.strategy.indicators import technical
from crypto_platform.data.manager import get_data_manager

log = Logger('Strategy')


class Strategy(object):

    def __init__(self):
        super(Strategy, self).__init__()
        self._indicators = []
        self._datasets = []
        self._extra_init = lambda context: None
        self._extra_handle = lambda context, data: None
        self._extra_analyze = lambda context, results: None

    def init(self, f):
        self._extra_init = f

    def handle_data(self, f):
        self._extra_handle = f

    def analyze(self, f):
        self._extra_analyze = f

    def _init_func(self, context, config=None):
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

        for d in self._datasets:
            d.fetch_data()

        self._extra_init(context)

    def _process_data(self, context, data):
        price = data.current(context.asset, 'price')
        cash = context.portfolio.cash
        record(price=price, cash=cash)

        context.price = price
        # Get price, open, high, low, close
        context.prices = data.history(
            context.asset,
            bar_count=context.BARS,
            fields=['price', 'open', 'high', 'low', 'close'],
            frequency='1d',
        )

        for d in self._datasets:
            d.record_data(context, data)

        for i in self._indicators:
            i.calculate(context.prices)
            i.record()

        self._extra_handle(context, data)
        self.weigh_signals(context, data)

    def _analyze(self, context, results):
        strat_plots = len(self._indicators) + len(self._datasets)
        pos = viz.get_start_geo(strat_plots + 2)
        viz.plot_percent_return(results, pos=pos)
        viz.plot_benchmark(results, pos=pos)
        plt.legend()
        pos += 1
        for i in self._indicators:
            i.plot(results, pos)
            pos += 1

        for d in self._datasets:
            d.plot(results, pos)
            pos += 1

        viz.plot_buy_sells(results, pos=pos)

        self._extra_analyze(context, results)
        # viz.add_legend()
        viz.show_plot()

    def add_indicator(self, indicator, priority=0, **kw):
        ind_class = getattr(technical, indicator)
        indicator = ind_class(**kw)
        self._indicators.insert(priority, indicator)

    def use_dataset(self, dataset_name, columns):
        data_manager = get_data_manager(dataset_name)(columns=columns)
        self._datasets.append(data_manager)


    def weigh_signals(self, context, data):
        sells, buys = 0, 0
        for i in self._indicators:
            if i.signals_buy:
                buys += 1
            elif i.signals_sell:
                sells += 1

        if buys > sells:
            self.place_buy(context)
        elif sells > buys:
            self.place_sell(context)


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
    def run(self):

        try:
            run_algorithm(
                capital_base=CONFIG.CAPITAL_BASE,
                data_frequency=CONFIG.DATA_FREQUENCY,
                initialize=self._init_func,
                handle_data=self._process_data,
                analyze=self._analyze,
                exchange_name=CONFIG.BUY_EXCHANGE,
                base_currency=CONFIG.BASE_CURRENCY,
                start=CONFIG.START,
                end=CONFIG.END,
            )
        except PricingDataNotLoadedError:
            log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)
