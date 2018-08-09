import json
import uuid
import shutil
import os
import inspect
import datetime
import copy
import logbook
import matplotlib.pyplot as plt
import pandas as pd
from rq import get_current_job

from catalyst import run_algorithm
from catalyst.api import symbol, set_benchmark, record, order, order_target_percent, cancel_order, get_datetime
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from kryptos.utils import load, viz, outputs
from kryptos.strategy.indicators import technical, ml
from kryptos.strategy.signals import utils as signal_utils
from kryptos.data.manager import get_data_manager
from kryptos import logger_group
from kryptos.settings import DEFAULT_CONFIG
from kryptos.settings import MLConfig as CONFIG
from kryptos.analysis import quant


class StratLogger(logbook.Logger):

    def __init__(self, strat):
        self.strat = strat
        super().__init__(name="STRATEGY")

    def process_record(self, record):
        logbook.Logger.process_record(self, record)
        record.extra["trade_date"] = self.strat.current_date

        if self.strat.in_job:
            job = get_current_job()
            job.meta['Strategy'] = record.msg
            job.save_meta()


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
        self._ml_models = []
        self.signals = {}
        self._datasets = {}
        self._extra_init = lambda context: None
        self._extra_handle = lambda context, data: None
        self._extra_analyze = lambda context, results, pos: None
        self._extra_plots = 0
        self.viz = True
        self.quant_results = None
        self.in_job = False

        self._signal_buy_funcs = []
        self._signal_sell_funcs = []

        # from JSON obj
        self._buy_signal_objs = []
        self._sell_signal_objs = []

        self._override_indicator_signals = False

        self._buy_func = None
        self._sell_func = None

        self.trading_info.update(kw)
        self.is_live = False

        self.log = StratLogger(self)
        logger_group.add_logger(self.log)

        self.current_date = None

    def serialize(self):
        d = {
            "trading": self.trading_info,
            "datasets": self.dataset_info,
            "indicators": self.indicator_info,
            "signals": self._dump_signals(),
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

    def signal_sell(self, override=False):
        """
        Calls the wrapped function when weighing signals to define extra signal logic

        Args:
            override: don't weigh any indicator default signals
        """
        self._override_indicator_signals = override

        def decorator(f):
            self._signal_sell_funcs.append(f)
            return f

        return decorator

    def signal_buy(self, override=False):
        """
        Calls the wrapped function when weighing signals to define extra signal logic

        Args:
            override: don't weigh any indicator default signals
        """
        self._override_indicator_signals = override

        def decorator(f):
            self._signal_buy_funcs.append(f)
            return f

        return decorator

    def _load_indicators(self, strat_dict):
        indicators = strat_dict.get("indicators", {})
        for i in indicators:
            if i.get("dataset") in [None, "market"]:
                ind = technical.get_indicator(**i)
                if ind not in self._market_indicators:
                    self.add_market_indicator(ind)

    def _load_datasets(self, strat_dict):
        datasets = strat_dict.get("datasets", {})
        for ds in datasets:
            self.use_dataset(ds["name"], ds["columns"])
            for i in ds.get("indicators", []):
                self.add_data_indicator(ds["name"], i["name"], col=i["symbol"])

    def _dump_signals(self):
        res = {}
        res['buy'] = self._buy_signal_objs
        res['sell'] = self._sell_signal_objs
        return res

    def _load_signals(self, strat_dict):
        signals = strat_dict.get('signals', {})
        for s in signals.get('buy', []):
            sig_func = getattr(signal_utils, s['func'], None)
            if not sig_func:
                raise Exception('JSON defined signals require a defined function')

            # store json repr so we can load params during execution
            self._buy_signal_objs.append(s)

        for s in signals.get('sell', []):
            sig_func = getattr(signal_utils, s['func'], None)
            if not sig_func:
                raise Exception('JSON defined signals require a defined function')

            # store json repr so we can load params during execution
            self._sell_signal_objs.append(s)

    def load_from_dict(self, strat_dict):
        trade_config = strat_dict.get("trading", {})
        self.trading_info.update(trade_config)
        # For all trading pairs in the poloniex bundle, the default denomination
        # currently supported by Catalyst is 1/1000th of a full coin. Use this
        # constant to scale the price of up to that of a full coin if desired.
        if self.trading_info["EXCHANGE"] == "poloniex":
            self.trading_info["TICK_SIZE"] = 1000.0

        self._load_indicators(strat_dict)
        self._load_datasets(strat_dict)
        self._load_signals(strat_dict)

    def load_from_json(self, json_file):
        with open(json_file, "r") as f:
            d = json.load(f)
            self.load_from_dict(d)

    def _init_func(self, context):
        """Sets up catalyst's context object and fetches external data"""
        context.asset = symbol(self.trading_info["ASSET"])
        if not self.is_live:
            set_benchmark(context.asset)
        context.i = 0
        context.errors = []
        for k, v in self.trading_info.items():
            if "__" not in k:
                setattr(context, k, v)

        for dataset, manager in self._datasets.items():
            manager.fetch_data()

        self._extra_init(context)
        self.log.info("Initilized Strategy")
        if context.DATA_FREQ == 'minute': # TODO: delete condition
            context.BARS = int(context.BARS * 24 * 60 / int(24*60/int(context.MINUTE_FREQ)))

    def _process_data(self, context, data):
        """Called at each algo iteration

        Calculates indicators, processes signals, and
        records market and external data

        Arguments:
            context {pandas.Dataframe} -- Catalyst context object
            data {pandas.Datframe} -- Catalyst data object
        """
        context.i += 1

        # Update actual context.price
        context.current = data.current(assets=context.asset,
                    fields=["close", "price", "open", "high", "low", "volume"])
        context.price = context.current.price
        record(price=context.price, cash=context.portfolio.cash, volume=context.current.volume)

        # To check to apply stop-loss, take-profit or keep position
        self.check_open_positions(context)

        # Filter minute frequency
        if (context.i - 1) % int(context.MINUTE_FREQ) != int(context.MINUTE_TO_OPERATE):
            return

        # set date first for logging purposes
        self.current_date = context.blotter.current_dt.date()

        if self.in_job:
            job = get_current_job()
            job.meta['date'] = self.current_date
            job.save_meta()

        self.log.debug("Processing algo iteration")
        for i in context.blotter.open_orders:
            self.log.debug("Canceling unfilled open order {}".format(i))
            cancel_order(i)

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

        # Filter historic data according to minute frequency
        # for the freq alias:
        # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
        filter_dates = pd.date_range(start=context.prices.iloc[0].name,
                            end=context.prices.iloc[-1].name,
                            freq=str(context.MINUTE_FREQ)+"min")
        context.prices = context.prices.loc[filter_dates]

        # Add current values to historic
        context.prices.loc[get_datetime()] = context.current

        if self._ml_models:
            # Add external datasets (Google Search Volume and Blockchain Info) as features
            for i in self._ml_models:
                for dataset, manager in self._datasets.items():
                    context.prices.index.tz = None
                    context.prices = pd.concat([context.prices, manager.df], axis=1, join_axes=[context.prices.index])
                i.calculate(context.prices)

        else:
            for dataset, manager in self._datasets.items():
                manager.calculate(context)
                manager.record_data(context)

        for i in self._market_indicators:
            try:
                i.calculate(context.prices)
                i.record()
            except Exception as e:
                self.log.error(e)
                self.log.error('Error calculating {}, skipping...'.format(i.name))

        self._extra_handle(context, data)
        self._count_signals(context, data)

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

        if not self._ml_models:
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
        ending_cash = results.cash[-1]
        self.log.info('Ending cash: ${}'.format(ending_cash))
        self.log.info('Completed for {} trading periods'.format(context.i))
        try:
            if self.viz:
                self._make_plots(context, results)
                quant.dump_plots_to_file(self.name, results)
        except:
            pass

        self.quant_results = quant.dump_summary_table(self.name, self.trading_info, results)

        for i in self._ml_models:
            i.analyze(self.name)

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
        if not self._ml_models:
            data_manager = self._datasets[dataset]
            data_manager.attach_indicator(indicator, col)

    def add_ml_models(self, indicator):
        """Use ML models to take decissions"""
        if isinstance(indicator, str):
            indicator = ml.get_indicator(indicator)
        self._ml_models.append(indicator)

    def use_dataset(self, dataset_name, columns):
        """Registers an external dataset to be integrated into algo"""
        if self._ml_models:
            # Using from CONFIG.START date - CONFIG.BARS days to CONFIG.END date
            config = copy.deepcopy(self.trading_info)
            config['START'] = (datetime.datetime.strptime(config['START'], '%Y-%m-%d') + datetime.timedelta(days=-config['BARS'])).strftime("%Y-%m-%d")
            data_manager = get_data_manager(dataset_name, cols=columns, config=config)
        else:
            data_manager = get_data_manager(dataset_name, cols=columns, config=self.trading_info)
        self._datasets[dataset_name] = data_manager

    def _get_kw_from_signal_params(self, sig_params, func):
        """Returns a dict of arguments to be passed to a signals util function"""
        kwargs = {}
        func_spec = inspect.getfullargspec(func)

        for arg in func_spec.args:

            if isinstance(sig_params[arg], int):
                kwargs[arg] = sig_params[arg]

            # use a specific output column
            # MY_BBANDS.middleband
            elif '.' in sig_params[arg]:
                [indicator_label, output] = sig_params[arg].split('.')
                indicator = self.indicator(indicator_label)
                output_col = indicator.outputs[output]
                kwargs[arg] = output_col

            # use label as output col if only "real" output
            else:
                indicator_label = sig_params[arg]
                indicator = self.indicator(indicator_label)
                kwargs[arg] = indicator.outputs[indicator_label]
        return kwargs

    def _construct_signal(self, obj):
        func = getattr(signal_utils, obj['func'])
        params = obj.get('params', {})

        kwargs = self._get_kw_from_signal_params(params, func)
        self.log.info('Calculating {}'.format(func.__name__))
        return func(**kwargs)

    def _calculate_custom_signals(self, context, data):
        sells, buys, neutrals = 0, 0, 0
        for i in self._buy_signal_objs:
            if self._construct_signal(i):
                buys += 1
                self.log.debug("Custom: BUY")
            else:
                neutrals += 1

        for i in self._sell_signal_objs:
            if self._construct_signal(i):
                sells += 1
                self.log.debug("Custom: SELL")
            else:
                neutrals += 1

        return sells, buys, neutrals


    def _count_signals(self, context, data):
        """Processes indicator to determine buy/sell opportunities"""

        sells, buys, neutrals = self._calculate_custom_signals(context, data)

        for f in self._signal_buy_funcs:
            if f(context, data):
                self.log.debug("Custom: BUY")
                buys += 1
            else:
                neutrals += 1

        for f in self._signal_sell_funcs:
            if f(context, data):
                self.log.debug("Custom: SELL")
                sells += 1
            else:
                neutrals += 1

        if self._override_indicator_signals:
            return self._weigh_signals(context, buys, sells, neutrals)

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

        for i in self._ml_models:
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

        self._weigh_signals(context, buys, sells, neutrals)

    def _weigh_signals(self, context, buys, sells, neutrals):
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
            self.log.warn("Skipping signaled sell due b/c no position")
            return

        self.log.info("Making Sell Order")
        if self._sell_func is None:
            return self._default_sell(context)

        self._sell_func(context)

    def check_open_positions(self, context):
        """Check open positions to sell to take profit or to stop loss.
        """
        if context.asset in context.portfolio.positions:
            position = context.portfolio.positions.get(context.asset)
            # self.log.info('Checking open positions: {amount} positions with cost basis {cost_basis} at {date} with price: {price}'.format(amount=position.amount, cost_basis=position.cost_basis, date=get_datetime(), price=context.price))

            if context.price >= position.cost_basis * (1 + CONFIG.TAKE_PROFIT): # Take Profit
                self._take_profit_sell(context, position.amount)

            if context.price < position.cost_basis * (1 - CONFIG.STOP_LOSS): # Stop Loss
                self._stop_loss_sell(context, position.amount)

    def _take_profit_sell(self, context, amount):
        order(
            asset=context.asset,
            amount=-amount,
            limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED),
        )

        position = context.portfolio.positions.get(context.asset)
        profit = (context.price * amount) - (position.cost_basis * amount)
        self.log.info("Sold {amount} @ {price} Profit: {profit}; Produced by take-profit signal at {date}".format(
                amount=amount, price=context.price, profit=profit, date=get_datetime()))

    def _stop_loss_sell(self, context, amount):
        order(
            asset=context.asset,
            amount=-amount,
            # limit_price=context.price * (1 - context.SLIPPAGE_ALLOWED),
        )

        position = context.portfolio.positions.get(context.asset)
        profit = (context.price * amount) - (position.cost_basis * amount)
        self.log.info("Sold {amount} @ {price} Profit: {profit}; Produced by stop-loss signal at {date}".format(
                amount=amount, price=context.price, profit=profit, date=get_datetime()))

    def _default_buy(self, context, size=None, price=None, slippage=None):
        position = context.portfolio.positions.get(context.asset)
        if position is None:
            order(
                asset=context.asset,
                amount=context.ORDER_SIZE,
                limit_price=context.price * (1 + context.SLIPPAGE_ALLOWED)
            )
            self.log.info(
                "Bought {amount} @ {price}".format(amount=context.ORDER_SIZE, price=context.price)
            )
        else:
            self.log.warn("Skipping signaled buy due to open position: {amount} positions with cost basis {cost_basis}".format(
                            amount=position.amount, cost_basis=position.cost_basis))

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


    def run(self, live=False, simulate_orders=True, viz=True, as_job=False):
        """Executes the trade strategy as a catalyst algorithm

        Basic algorithm behavior is defined cia the config object, while
        iterative logic is managed by the Strategy object.
        """
        self.in_job = as_job
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
        self.log.info('Running live trading, suimulating orders: {}'.format(simulate_orders))
        self.is_live = True
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
