import json
import uuid

import logbook
import matplotlib.pyplot as plt
import pandas as pd

from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record, order, order_target_percent, cancel_order
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from kryptos.platform.utils import load, viz
from kryptos.platform.strategy.indicators import technical
from kryptos.platform.data.manager import get_data_manager
from kryptos.platform import logger_group
from kryptos.platform.settings import DEFAULT_CONFIG
from kryptos.platform.analysis import quant


class StratLogger(logbook.Logger):

    def __init__(self, strat):
        self.strat = strat
        super().__init__(name="STRATEGY")

    def process_record(self, record):
        logbook.Logger.process_record(self, record)
        record.extra["trade_date"] = self.strat.current_date


class Strategy(object):

    def __init__(self, name=None, **kw):
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

        # name required for storing live algos
        if name is None:
            name = "Strat-" + str(uuid.uuid1())

        self.name = name
        self.trading_info = DEFAULT_CONFIG
        self._market_indicators = []
        self.signals = {}
        self._datasets = {}
        self._extra_init = lambda context: None
        self._extra_handle = lambda context, data: None
        self._extra_analyze = lambda context, results, pos: None
        self._extra_plots = 0
        self.viz = True
        self.quant_results = None

        self._signal_buy_func = lambda context, data: None
        self._signal_sell_func = lambda context, data: None

        self._buy_func = None
        self._sell_func = None

        self.trading_info.update(kw)

        self.log = StratLogger(self)
        logger_group.add_logger(self.log)

        self.current_date = None

    def serialize(self):
        d = {
            "trading": self.trading_info,
            "datasets": self.dataset_info,
            "indicators": self.indicator_info,
            "signals": self.signals,
        }
        return json.dumps(d, indent=3)

    @property
    def indicator_info(self):
        inds = []
        for i in self._market_indicators:
            inds.append(i.serialize())
        return inds

    def indicator(self, label):
        for i in self._market_indicators:
            if i.label == label.upper():
                return i

    @property
    def dataset_info(self):
        info = []
        for dataset, manag in self._datasets.items():
            info.append(manag.serialize())
        return info

    def init(self, f):
        """Calls the wrapped function before catalyst algo begins"""
        self._extra_init = f

    def handle_data(self, f):
        """Calls the wrapped function at each algo iteration"""
        self._extra_handle = f

    def analyze(self, num_plots=0):
        """Calls the wrapped function after algo has finished"""
        self._extra_plots += num_plots

        def decorator(f):
            self._extra_analyze = f
            return f

        return decorator

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

    def load_from_dict(self, strat_dict):
        trade_config = strat_dict.get("trading", {})
        self.trading_info.update(trade_config)
        # For all trading pairs in the poloniex bundle, the default denomination
        # currently supported by Catalyst is 1/1000th of a full coin. Use this
        # constant to scale the price of up to that of a full coin if desired.
        if self.trading_info["EXCHANGE"] == "poloniex":
            self.trading_info["TICK_SIZE"] = 1000.0

        indicators = strat_dict.get("indicators", {})
        for i in indicators:
            if i.get("dataset") in [None, "market"]:
                ind = technical.get_indicator(**i)
                if ind not in self._market_indicators:
                    self.add_market_indicator(ind)

        datasets = strat_dict.get("datasets", {})
        for ds in datasets:
            self.use_dataset(ds["name"], ds["columns"])
            for i in ds.get("indicators", []):
                self.add_data_indicator(ds["name"], i["name"], col=i["symbol"])

    def load_from_json(self, json_file):
        with open(json_file, "r") as f:
            d = json.load(f)
            self.load_from_dict(d)

    def _init_func(self, context):
        """Sets up catalyst's context object and fetches external data"""
        context.asset = symbol(self.trading_info["ASSET"])
        context.market = symbol(self.trading_info["ASSET"])
        set_benchmark(context.asset)
        context.ORDER_SIZE = 0.5
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365
        context.errors = []
        for k, v in self.trading_info.items():
            if "__" not in k:
                setattr(context, k, v)

        for dataset, manager in self._datasets.items():
            manager.fetch_data()

        self._extra_init(context)
        self.log.info("Initilized Strategy")

    def _process_data(self, context, data):
        """Called at each algo iteration

        Calculates indicators, processes signals, and
        records market and external data

        Arguments:
            context {pandas.Dataframe} -- Catalyst context object
            data {pandas.Datframe} -- Catalyst data object
        """
        # set date first for logging purposes
        self.current_date = context.blotter.current_dt.date()

        self.log.debug("Processing algo iteration")
        for i in context.blotter.open_orders:
            self.log.debug("Canceling unfilled open order {}".format(i))
            cancel_order(i)

        price = data.current(context.asset, "price")
        volume = data.current(context.asset, "volume")
        cash = context.portfolio.cash
        record(price=price, cash=cash, volume=volume)

        context.price = price

        # Get price, open, high, low, close
        # The frequency attribute determine the bar size. We use this convention
        # for the frequency alias:
        # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
        context.prices = data.history(
            context.asset,
            bar_count=context.BARS,
            fields=["price", "open", "high", "low", "close", "volume"],
            frequency=context.HISTORY_FREQ,
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

        return len(self._market_indicators) + len(self._datasets) + dataset_inds + self._extra_plots

    def _make_plots(self, context, results):
        # strat_plots = len(self._market_indicators) + len(self._datasets)
        pos = viz.get_start_geo(self.total_plots + 3)
        viz.plot_percent_return(results, pos=pos)
        viz.plot_benchmark(results, pos=pos)
        plt.legend()
        pos += 1

        viz.plot_column(results, "cash", pos=pos)
        # viz.plot_bar(results, 'volume', pos=pos, label='volume', twin=ax)

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

        self._extra_analyze(context, results, pos)
        pos += self._extra_plots

        viz.plot_buy_sells(results, pos=pos)
        viz.show_plot()

    def _analyze(self, context, results):
        """Plots results of algo performance, external data, and indicators"""
        if self.viz:
            self._make_plots(context, results)
            quant.dump_plots_to_file(self.name, results)

        self.quant_results = quant.dump_summary_table(self.name, self.trading_info, results)


    def add_market_indicator(self, indicator, priority=0, **params):
        """Registers an indicator to be applied to standard OHLCV exchange data"""
        if isinstance(indicator, str):
            indicator = technical.get_indicator(indicator, **params)
        # ind_class = getattr(technical, indicator)
        # indicator = ind_class(**kw)
        self._market_indicators.insert(priority, indicator)

    def add_data_indicator(self, dataset, indicator, col=None):
        """Registers an indicator to be called on external data"""
        if dataset not in self._datasets:
            raise LookupError(
                "{} dataset not registered, register with .use_dataset() before adding indicators"
            )

        data_manager = self._datasets[dataset]
        data_manager.attach_indicator(indicator, col)

    def use_dataset(self, dataset_name, columns):
        """Registers an external dataset to be integrated into algo"""
        data_manager = get_data_manager(dataset_name, cols=columns, config=self.trading_info)
        self._datasets[dataset_name] = data_manager

    def weigh_signals(self, context, data):
        """Processes indicator to determine buy/sell opportunities"""
        sells, buys, neutrals = 0, 0, 0
        for i in self._market_indicators:
            if i.outputs is None:
                continue
            if i.signals_buy:
                self.log.debug("{}: BUY".format(i.name))
                buys += 1
            elif i.signals_sell:
                self.log.debug("{}: SELL".format(i.name))
                sells += 1
            else:
                neutrals += 1

        for d, manager in self._datasets.items():
            for i in manager._indicators:
                if i.signals_buy:
                    self.log.debug("{}: BUY".format(i.name))
                    buys += 1
                elif i.signals_sell:
                    self.log.debug("{}: SELL".format(i.name))
                    sells += 1
                else:
                    neutrals += 1

        if self._signal_buy_func(context, data):
            self.log.debug("Custom: BUY")
            buys += 1
        elif self._signal_sell_func(context, data):
            self.log.debug("Custom: SELL")
            sells += 1
        else:
            neutrals += 1

        self.log.debug(
            "Buy signals: {}, Sell signals: {}, Neutral Signals: {}".format(buys, sells, neutrals)
        )
        if buys > sells:
            self.log.debug("Signaling to buy")
            self.make_buy(context)
        elif sells > buys:
            self.log.debug("Signaling to sell")
            self.make_sell(context)

    def make_buy(self, context):
        if context.portfolio.cash < context.price * context.ORDER_SIZE:
            self.log.warn(
                "Skipping signaled buy due to cash amount: {} < {}".format(
                    context.portfolio.cash, (context.price * context.ORDER_SIZE)
                )
            )
            return

        self.log.info("Making Buy Order")
        if self._buy_func is None:
            return self._default_buy(context)

        self._buy_func(context)

    def make_sell(self, context):
        if context.asset not in context.portfolio.positions:
            self.log.debug("Skipping signaled sell due b/c no position")
            return

        self.log.info("Making Sell Order")
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
            self.log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )

    def _default_sell(self, context, size=None, price=None, slippage=None):
        position = context.portfolio.positions.get(context.asset)
        if position == 0:
            self.log.debug("Position Zero")
            return

        # Cost Basis
        cost_basis = position.cost_basis
        self.log.info(
            "Holdings: {amount} @ {cost_basis}".format(
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
        self.log.info(
            "Sold {amount} @ {price} Profit: {profit}".format(
                amount=position.amount, price=context.price, profit=profit
            )
        )

    # Save the prices and analysis to send to analyze

    def run(self, live=False, simulate_orders=True, viz=True):
        """Executes the trade strategy as a catalyst algorithm

        Basic algorithm behavior is defined cia the config object, while
        iterative logic is managed by the Strategy object.
        """

        self.viz = viz
        try:
            if live or self.trading_info.get("LIVE", False):
                self.run_live(simulate_orders=simulate_orders)
            else:
                self.run_backtest()

        except PricingDataNotLoadedError:
            self.log.warn("Ingesting required exchange bundle data")
            load.ingest_exchange(self.trading_info)
            self.log.warn("Exchange ingested, please run the command again")

    def run_backtest(self):
        try:
            run_algorithm(
                algo_namespace=self.name,
                capital_base=self.trading_info["CAPITAL_BASE"],
                data_frequency=self.trading_info["DATA_FREQ"],
                initialize=self._init_func,
                handle_data=self._process_data,
                analyze=self._analyze,
                exchange_name=self.trading_info["EXCHANGE"],
                quote_currency=self.trading_info["BASE_CURRENCY"],
                start=pd.to_datetime(self.trading_info["START"], utc=True),
                end=pd.to_datetime(self.trading_info["END"], utc=True),
            )
        except KeyError as e:
            self.log.exception(e)
            self.log.error(
                "The configured timeframe seems to be causing an error. Consider adjusting the start date",
                e,
            )

    def run_live(self, simulate_orders=True):
        # import pdb; pdb.set_trace()
        run_algorithm(
            capital_base=self.trading_info["CAPITAL_BASE"],
            initialize=self._init_func,
            handle_data=self._process_data,
            analyze=self._analyze,
            exchange_name=self.trading_info["EXCHANGE"],
            live=True,
            algo_namespace=self.name,
            quote_currency=self.trading_info["BASE_CURRENCY"],
            live_graph=False,
            simulate_orders=simulate_orders,
            stats_output=None,
        )
