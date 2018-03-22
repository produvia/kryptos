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
        """Central interface used to build and execute trading strategies
        
        Strategy objects represent a high level interface for constructing
        malleable trading algroithms defined by provided inputs.

        Strategies are repsonsible:
            - applying trade strategy inputs to the catalyst algorithm context
            - integrating external datasets
            - declaring and calculating indicators
            - making trade decisions based on signals

        Three decorators are provided to perform other logic,
        such as modifying Strategy objects, throghout algo execution.

            @init - before algo starts
            @handle_data - at each algo iteration
            @analyze - after algo has completed

        The underlying logic of algorithm execution (market data, making orders,
        persisting data, and iterating through timeseries data) is handled by catalyst.
        """

        self._market_indicators = []
        self._datasets = {}
        self._extra_init = lambda context: None
        self._extra_handle = lambda context, data: None
        self._extra_analyze = lambda context, results: None

    def init(self, f):
        """Calls the wrapped function before catalyst algo begins"""
        self._extra_init = f

    def handle_data(self, f):
        """Calls the wrapped function at each algo iteration"""
        self._extra_handle = f

    def analyze(self, f):
        """Calls the wrapped function after algo has finished"""
        self._extra_analyze = f

    def _init_func(self, context, config=None):
        """Sets up catalyst's context object and fetches external data"""
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

        for dataset, manager in self._datasets.items():
            manager.fetch_data()

        self._extra_init(context)

    def _process_data(self, context, data):
        """Called at each algo iteration

        Calculates indicators, processes signals, and
        records market and external data

        Arguments:
            context {pandas.Dataframe} -- Catalyst context object
            data {pandas.Datframe} -- Catalyst data object
        """
        price = data.current(context.asset, 'price')
        cash = context.portfolio.cash
        record(price=price, cash=cash)

        context.price = price
        # Get price, open, high, low, close
        context.prices = data.history(
            context.asset,
            bar_count=context.BARS,
            fields=['price', 'open', 'high', 'low', 'close', 'volume'],
            frequency='1d',
        )

        for dataset, manager in self._datasets.items():
            manager.calculate(context)
            manager.record_data(context)

        for i in self._market_indicators:
            i.calculate(context.prices)
            i.record()

        self._extra_handle(context, data)
        self.weigh_signals(context, data)

    def _analyze(self, context, results):
        """Plots results of algo performance, external data, and indicators"""
        strat_plots = len(self._market_indicators) + len(self._datasets)
        pos = viz.get_start_geo(strat_plots + 2)
        viz.plot_percent_return(results, pos=pos)
        viz.plot_benchmark(results, pos=pos)
        plt.legend()
        pos += 1
        for i in self._market_indicators:
            i.plot(results, pos)
            pos += 1

        for dataset, manager in self._datasets.items():
            manager.plot(results, pos)
            pos += 1

        viz.plot_buy_sells(results, pos=pos)

        self._extra_analyze(context, results)
        # viz.add_legend()
        viz.show_plot()

    def add_market_indicator(self, indicator, priority=0, **kw):
        """Registers an indicator to be applied to standard OHLCV exchange data"""
        indicator = technical.get_indicator(indicator)
        # ind_class = getattr(technical, indicator)
        # indicator = ind_class(**kw)
        self._market_indicators.insert(priority, indicator)

    def add_data_indicator(self, dataset, indicator, cols=None):
        """Registers an indicator to be called on external data"""
        if dataset not in self._datasets:
            raise LookupError

        data_manager = self._datasets[dataset]
        data_manager.attach_indicator(indicator, cols)

    def use_dataset(self, dataset_name, columns):
        """Registers an external dataset to be integrated into algo"""
        data_manager = get_data_manager(dataset_name)(columns=columns)
        self._datasets[dataset_name] = data_manager

    def weigh_signals(self, context, data):
        """Processes indicator to determine buy/sell opportunities"""
        sells, buys = 0, 0
        for i in self._market_indicators:
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
        """Executes the trade strategy as a catalyst algorithm

        Basic algorithm behavior is defined cia the config object, while
        iterative logic is managed by the Strategy object.
        """
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
            log.info('Exchange ingested, please run the command again')
