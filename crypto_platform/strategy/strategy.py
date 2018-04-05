from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record, order, order_target_percent, get_open_orders, cancel_order
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError
import logbook
import matplotlib.pyplot as plt
import json

from crypto_platform.config import CONFIG
from crypto_platform.utils import load, viz
from crypto_platform.strategy.indicators import technical
from crypto_platform.data.manager import get_data_manager

log = logbook.Logger('Strategy')
log.level = logbook.INFO


class Strategy(object):

    def __init__(self, name=None):
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

        self.name = name
        self._market_indicators = []
        self._datasets = {}
        self._extra_init = lambda context: None
        self._extra_handle = lambda context, data: None
        self._extra_analyze = lambda context, results: None

        self._signal_buy_func = lambda context, data: None
        self._signal_sell_func = lambda context, data: None

        self._buy_func = None
        self._sell_func = None

    def serialize(self):
        d = {
        'indicators': self.indicators,
        }
        return json.dumps(d, indent=3)

    @property
    def indicators(self):
        inds = []
        for i in self._market_indicators:
            inds.append(i.serialize())
        return inds


    def init(self, f):
        """Calls the wrapped function before catalyst algo begins"""
        self._extra_init = f

    def handle_data(self, f):
        """Calls the wrapped function at each algo iteration"""
        self._extra_handle = f

    def analyze(self, f):
        """Calls the wrapped function after algo has finished"""
        self._extra_analyze = f

    def buy_order(self, f):
        """Calls the wrapped function if indicators signal to buy"""
        self._buy_func = f

    def sell_order(self, f):
        """Calls the wrapped function if indicators signal to sell"""
        self._sell_func = f

    def signal_sell(self, f):
        """Calls the wrapped function when weighing signals to define extra signal logic"""
        self._signal_sell_func = f

    def signal_buy(self, f):
        """Calls the wrapped function when weighing signals to define extra signal logic"""
        self._signal_buy_func = f

    def load_from_json(self, json_file):
        with open(json_file, 'r') as f:
            d = json.load(f)

        for i in d['indicators']:
            if i.get('dataset') in [None, 'market']:
                ind = technical.get_indicator(**i)
                self.add_market_indicator(ind)

            elif i.get('dataset') is not None:
                cols, dataset, name = i['cols'], i['dataset'], i['name']

                self.add_data_indicator(dataset, name, cols=cols)

    def _init_func(self, context, config=None):
        """Sets up catalyst's context object and fetches external data"""
        if config is None:
            config = CONFIG
        context.asset = symbol(CONFIG.ASSET)
        context.market = symbol(CONFIG.ASSET)
        set_benchmark(context.asset)
        context.ORDER_SIZE = 0.5
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365
        context.errors = []
        for k, v in CONFIG.__dict__.items():
            if '__' not in k:
                setattr(context, k, v)

        for dataset, manager in self._datasets.items():
            manager.fetch_data()

        self._extra_init(context)
        log.info('Initilized Strategy')

    def _process_data(self, context, data):
        """Called at each algo iteration

        Calculates indicators, processes signals, and
        records market and external data

        Arguments:
            context {pandas.Dataframe} -- Catalyst context object
            data {pandas.Datframe} -- Catalyst data object
        """
        log.debug('Processing algo iteration')
        for i in get_open_orders(context.asset):
            log.warn('Canceling unfilled open order')
            cancel_order(i)

        price = data.current(context.asset, 'price')
        volume = data.current(context.asset, 'volume')
        cash = context.portfolio.cash
        record(price=price, cash=cash, volume=volume)

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

    @property
    def total_plots(self):
        dataset_inds = 0
        for d, m in self._datasets.items():
            dataset_inds += len(m._indicators)

        return len(self._market_indicators) + len(self._datasets) + dataset_inds


    def _analyze(self, context, results):
        """Plots results of algo performance, external data, and indicators"""
        # strat_plots = len(self._market_indicators) + len(self._datasets)
        pos = viz.get_start_geo(self.total_plots + 3)
        viz.plot_percent_return(results, pos=pos)
        viz.plot_benchmark(results, pos=pos)
        pos += 1
        viz.plot_column(results, 'cash', pos=pos)
        # viz.plot_bar(results, 'volume', pos=pos, label='volume', twin=ax)
        plt.legend()
        pos += 1
        for i in self._market_indicators:
            i.plot(results, pos)
            pos += 1

        for dataset, manager in self._datasets.items():
            manager.plot(results, pos, skip_indicators=True)
            pos += 1
            for i in manager._indicators:
                i.plot(results, pos)
                pos += 1

        viz.plot_buy_sells(results, pos=pos)

        self._extra_analyze(context, results)
        # viz.add_legend()
        viz.show_plot()

    def add_market_indicator(self, indicator, priority=0, **params):
        """Registers an indicator to be applied to standard OHLCV exchange data"""
        if isinstance(indicator, str):
            indicator = technical.get_indicator(indicator, **params)
        # ind_class = getattr(technical, indicator)
        # indicator = ind_class(**kw)
        self._market_indicators.insert(priority, indicator)

    def add_data_indicator(self, dataset, indicator, cols=None):
        """Registers an indicator to be called on external data"""
        if dataset not in self._datasets:
            self.use_dataset(dataset, cols)

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

        for d, manager in self._datasets.items():
            for i in manager._indicators:
                if i.signals_buy:
                    buys += 1
                elif i.signals_sell:
                    sells += 1

        if self._signal_buy_func(context, data):
            log.info('Custom signal to buy')
            buys += 1
        elif self._signal_sell_func(context, data):
            log.info('Custom signal to buy')
            sells += 1

        if buys > sells:
            log.info('Signaling to buy')
            self.make_buy(context)
        elif sells > buys:
            log.info('Signaling to sell')
            self.make_sell(context)


    def make_buy(self, context):
        if context.portfolio.cash < context.price * context.ORDER_SIZE:
            log.warn('Skipping signaled buy due to cash amount: {} < {}'.format(context.portfolio.cash, (context.price * context.ORDER_SIZE)))
            return
        if self._buy_func is None:
            return self._default_buy(context)
        self._buy_func(context)

    def make_sell(self, context):
        if self._sell_func is None:
            return self._default_sell(context)
        self._sell_func(context)


    def _default_buy(self, context, size=None, price=None, slippage=None):
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

    def _default_sell(self, context, size=None, price=None, slippage=None):
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
