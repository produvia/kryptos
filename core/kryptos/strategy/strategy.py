import json
import uuid
import os
import inspect
import datetime
import copy
from textwrap import dedent
import logbook
import time

import pandas as pd
import numpy as np
from rq import get_current_job
import arrow

from catalyst import run_algorithm
from catalyst.api import (
    symbol,
    set_benchmark,
    record,
    order,
    order_target_percent,
    cancel_order,
    get_datetime,
)
from catalyst.exchange.utils import stats_utils
from catalyst.exchange import exchange_errors
from ccxt.base import errors as ccxt_errors

from kryptos.utils import viz, tasks, auth, outputs
from kryptos.strategy.indicators import technical, ml
from kryptos.strategy.signals import utils as signal_utils
from kryptos.data.manager import get_data_manager
from kryptos import logger_group
from kryptos.settings import DEFAULT_CONFIG, TAKE_PROFIT, STOP_LOSS, PERF_DIR
from kryptos.analysis import quant

from redo import retry
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt


class StratLogger(logbook.Logger):
    def __init__(self, strat):
        self.strat = strat
        super().__init__(name="STRATEGY")

    def process_record(self, record):
        logbook.Logger.process_record(self, record)
        record.extra["trade_date"] = self.strat.current_date

        if self.strat.in_job:  # and record.level_name in ['INFO', 'NOTICE', 'WARN']:
            job = get_current_job()
            if not job.meta.get("output"):
                job.meta["output"] = record.msg
            else:
                job.meta["output"] += record.msg + "\n"
            job.save_meta()


class StratState(object):

    def __init__(self):
        self.i = 0

    def load_from_context(self, context):
        for k, v in context.state.items():
            setattr(self, k, v)

    def dump_to_context(self, context):
        context.state.update(self.__dict__)


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

        self.id = str(uuid.uuid1())

        # name required for storing live algos
        if name is None:
            name = "Strat-" + self.id

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

        self.telegram_id = None

        self._signal_buy_funcs = []
        self._signal_sell_funcs = []

        # from JSON obj
        self._buy_signal_objs = []
        self._sell_signal_objs = []

        self._override_indicator_signals = False

        self._buy_func = None
        self._sell_func = None

        self.trading_info.update(kw)

        self._live = False
        self._simulate_orders = True

        self.log = StratLogger(self)
        logger_group.add_logger(self.log)

        self.current_date = None
        self.last_date = None
        self.filter_dates = None
        self.date_init_reference = None
        self._context_ref = None
        self._state = StratState()

    @property
    def is_live(self):
        return self._live and not self._simulate_orders

    @property
    def is_paper(self):
        return self._live and self._simulate_orders

    @property
    def is_backtest(self):
        return not self._live

    @property
    def mode(self):
        if self.is_backtest:
            return "backtest"
        elif self.is_paper:
            return "paper"
        elif self.is_live:
            return "live"

    @property
    def state(self):
        return self._state

    def serialize(self):
        return json.dumps(self.to_dict(), indent=3)

    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "trading": self.trading_info,
            "datasets": self.dataset_info,
            "indicators": self.indicator_info,
            "models": self.model_info,
            "signals": self._dump_signals(),
        }
        return d

    @property
    def indicator_info(self):
        inds = []
        for i in self._market_indicators:
            inds.append(i.serialize())
        return inds

    @property
    def model_info(self):
        models = []
        for m in self._ml_models:
            models.append(m.serialize())
        return models

    @property
    def exchange(self):
        return self.trading_info.get("EXCHANGE")

    @exchange.setter
    def exchange(self, val):
        self.trading_info["EXCHANGE"] = val

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
                if not i.get("symbol"):
                    i["symbol"] = self.trading_info["ASSET"]
                ind = technical.get_indicator(**i)
                if ind not in self._market_indicators:
                    self.add_market_indicator(ind)

    def _load_ml_models(self, strat_dict):
        models = strat_dict.get("models", {})
        for m in models:
            if not m.get("symbol"):
                m["symbol"] = self.trading_info["ASSET"]
            model = ml.get_indicator(**m)
            self.add_ml_models(model)

    def _load_datasets(self, strat_dict):
        datasets = strat_dict.get("datasets", {})
        for ds in datasets:
            self.use_dataset(ds["name"], ds["columns"])
            for i in ds.get("indicators", []):
                self.add_data_indicator(ds["name"], i["name"], col=i["symbol"])

    def _dump_signals(self):
        res = {}
        res["buy"] = self._buy_signal_objs
        res["sell"] = self._sell_signal_objs
        return res

    def _load_signals(self, strat_dict):
        signals = strat_dict.get("signals", {})
        for s in signals.get("buy", []):
            sig_func = getattr(signal_utils, s["func"], None)
            if not sig_func:
                raise Exception("JSON defined signals require a defined function")

            # store json repr so we can load params during execution
            self._buy_signal_objs.append(s)

        for s in signals.get("sell", []):
            sig_func = getattr(signal_utils, s["func"], None)
            if not sig_func:
                raise Exception("JSON defined signals require a defined function")

            # store json repr so we can load params during execution
            self._sell_signal_objs.append(s)

    def _load_trading(self, strat_dict):
        trade_config = strat_dict.get("trading", {})
        self.trading_info.update(trade_config)
        # For all trading pairs in the poloniex bundle, the default denomination
        # currently supported by Catalyst is 1/1000th of a full coin. Use this
        # constant to scale the price of up to that of a full coin if desired.
        if self.trading_info["EXCHANGE"] == "poloniex":
            self.trading_info["TICK_SIZE"] = 1000.0

    def load_dict(self, strat_dict):
        self.name = strat_dict.get("name")
        self._load_trading(strat_dict)
        self._load_indicators(strat_dict)
        self._load_datasets(strat_dict)
        self._load_signals(strat_dict)
        self._load_ml_models(strat_dict)

    def load_json_file(self, json_file):
        with open(json_file, "r") as f:
            d = json.load(f)
            self.load_dict(d)

    @classmethod
    def from_dict(cls, strat_dict):
        instance = cls()
        instance.load_dict(strat_dict)
        return instance

    @classmethod
    def from_json_file(cls, json_file):
        instance = cls()
        instance.load_json_file(json_file)
        return instance

    def notify(self, msg):
        if self.telegram_id:
            tasks.queue_notification(msg, self.telegram_id)

    def _init_func(self, context):
        """Sets up catalyst's context object and fetches external data"""

        self._context_ref = context
        self.state.load_from_context(context)

        self.log.debug(f'Starting strategy on iteration {self.state.i}')


        self.state.asset = symbol(self.trading_info["ASSET"])
        if self.is_backtest:
            self.log.debug("Setting benchmark")
            set_benchmark(self.state.asset)

        for k, v in self.trading_info.items():
            if "__" not in k:
                setattr(self.state, k, v)

        if self._datasets.items():
            if self.state.DATA_FREQ == "daily":
                for dataset, manager in self._datasets.items():
                    manager.fetch_data()
            else:
                raise ValueError(
                    'Internal Error: Value of self.state.DATA_FREQ should be "minute" if you use Google Search Volume or Quandl datasets.'
                )

        self._extra_init(context)

        if self.in_job:
            job = get_current_job()
            if job.meta.get("PAUSED"):
                self.log.warning(f"Paused strategy {self.id} has been resumed")
                self.notify("Your strategy has resumed!")
                self.log.info(json.dumps(self.state))
                self.log.notice(f"resuming on trade iteration {self.state.i}")
                
            else:
                self.notify("Your strategy has started!")
                self.state.i = 0
                self.state.errors = []

        self.log.info("Initilized Strategy")
        self._check_configuration(context)

        # Set self.state.BARS size to work with custom minute frequency
        if self.state.DATA_FREQ == "minute":
            self.state.BARS = int(
                self.state.BARS * 24 * 60 / int(24 * 60 / int(self.state.MINUTE_FREQ))
            )

        self.date_init_reference = pd.Timestamp("2013-01-01 00:00:00", tz="utc") + pd.Timedelta(
            minutes=int(self.state.MINUTE_TO_OPERATE)
        )

        # Set commissions
        context.set_commission(maker=self.state.MAKER_COMMISSION, taker=self.state.TAKER_COMMISSION)
        self.state.dump_to_context(context)

    def _check_configuration(self, context):
        """Checking config.json valid values"""
        self._context_ref = context
        self.state.load_from_context(context)

        if self.state.DATA_FREQ != "minute" and self.state.DATA_FREQ != "daily":
            raise ValueError(
                'Internal Error: Value of self.state.DATA_FREQ should be "minute" or "daily"'
            )
        if self.state.DATA_FREQ == "minute":
            if self.state.HISTORY_FREQ[-1] != "T":
                raise ValueError(
                    'Internal Error: DATA_FREQ=="minute" the value of HISTORY_FREQ shoud be "<NUMBER>T". Example: "1T"'
                )
            if int(self.state.MINUTE_FREQ) % int(self.state.HISTORY_FREQ[:-1]) != 0:
                raise ValueError(
                    'Internal Error: When DATA_FREQ=="minute" HISTORY_FREQ shoud be divisible by MINUTE_FREQ'
                )
        elif self.state.DATA_FREQ == "daily":
            if self.state.HISTORY_FREQ[-1] != "d":
                raise ValueError(
                    'Internal Error: When DATA_FREQ=="minute" the value of HISTORY_FREQ shoud be "<NUMBER>d". Example: "1d"'
                )

        self.state.dump_to_context(context)

    def _set_current_fields(self, context, data):
        try:
            # In live mode, "volume", "close" and "price" are the only available fields.
            # In live mode, "volume" returns the last 24 hour trading volume.

            #  Update actual self.state.price
            if not self.is_backtest:
                self.state.current = data.current(
                    assets=self.state.asset, fields=["volume", "close", "price"]
                )
            else:
                self.state.current = data.current(
                    assets=self.state.asset,
                    fields=["open", "high", "low", "volume", "close", "price"],
                )
            self.state.price = self.state.current.price
            record(
                price=self.state.price,
                cash=context.portfolio.cash,
                volume=self.state.current.volume,
            )
            self.state.dump_to_context(context)
            return True

        except exchange_errors.NoValueForField as e:
            self.log.warn(e)
            self.log.warn(f"Skipping trade period: {e}")
            return False

        except KeyError:
            self.log.warn("Error when getting current fields")
            return False

        

    def _check_minute_freq(self, context, data):
        if self.state.DATA_FREQ == "minute":
            # Calcule the minutes between the last iteration (train dataset) and first iteration (test dataset)
            if self.last_date is None:
                last_date = self._get_last_date(context, data)
            else:
                last_date = self.last_date
            base_minutes = (self.current_date - last_date) / np.timedelta64(1, "m")
            if base_minutes != int(self.state.MINUTE_FREQ):
                return False

            if self.last_date is None:
                self.last_date = last_date

        return True

    def _fetch_history(self, context, data):
        # Get price, open, high, low, close
        # The frequency attribute determine the bar size. We use this convention
        # for the frequency alias:
        # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
        self.log.debug("Fetching history")
        self.state.prices = data.history(
            self.state.asset,
            bar_count=self.state.BARS,
            fields=["price", "open", "high", "low", "close", "volume"],
            frequency=self.state.HISTORY_FREQ,
        )

        self.state.dump_to_context(context)

    def _filter_fetched_history(self, context, data):
        # Filter historic data according to minute frequency
        # for the freq alias:
        # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
        if self.state.DATA_FREQ == "minute":
            filter_dates = pd.date_range(
                start=self.date_init_reference,
                end=self.state.prices.iloc[-1].name,
                freq=str(self.state.MINUTE_FREQ) + "min",
            )
            self.state.prices = self.state.prices.loc[filter_dates]
            self.state.prices = self.state.prices.dropna()

            if self.filter_dates is not None:
                self.filter_dates = self.filter_dates.append(
                    self.filter_dates.symmetric_difference(filter_dates)
                )
            else:
                self.filter_dates = filter_dates

            # Add current values to historic
            self.last_date = get_datetime()
            self.state.prices.loc[self.last_date] = self.state.current
            self.state.dump_to_context(context)

    def fetch_history(self, context, data):
        try:
            retry(
                self._fetch_history,
                sleeptime=5,
                retry_exceptions=(ccxt_errors.RequestTimeout),
                args=(context, data),
                cleanup=lambda: self.log.warn("CCXT request timed out, retrying..."),
            )
            return True

        except ccxt_errors.ExchangeNotAvailable:
            self.log.error(f"{self.exchange} API is currently unavailable, skipping trading step")
            return False

        except ccxt_errors.DDoSProtection:
            self.log.error("Hit Rate limit, skipping trade step")
            return False

        except SystemExit:
            self.log.warning('Not retrying history due to algo exit')
            return False

        except Exception:
            self.log.error("Could not fetch latest history", exec_info=True)
            return False

    def _enqueue_ml_calcs(self, context, data):
        #  Add external datasets (Google Search Volume and Blockchain Info) as features
        for i in self._ml_models:
            if self.state.DATA_FREQ == "daily":
                for dataset, manager in self._datasets.items():
                    self.state.prices.index.tz = None
                    self.state.prices = pd.concat(
                        [self.state.prices, manager.df], axis=1, join_axes=[self.state.prices.index]
                    )
            i.calculate(self.state.prices, self.name)

        self.state.dump_to_context(context)

    def _process_data(self, context, data):
        """Called at each algo iteration

        Calculates indicators, processes signals, and
        records market and external data

        Arguments:
            context {pandas.Dataframe} -- Catalyst context object
            data {pandas.Datframe} -- Catalyst data object
        """

        # catalyst dumps pickle file after handle_data called
        # so this call uploads the state of
        # the previously compelted iteration
        outputs.upload_state_to_storage(self)


        self.state.i += 1

        # uses context.end because to get algo's exact time end
        # which was passed to run_algorithm
        end = arrow.get(context.end)
        # now = arrow.utcnow()
        time_left = end.humanize(only_distance=True)
        self.log.debug(f"Stopping strategy in {time_left}")

        # the following called methods return:
        # True if the iteration should continued
        # False if the algo should not continue

        if not self._set_current_fields(context, data):
            return

        # To check to apply stop-loss, take-profit or keep position
        self.check_open_positions(context)

        # set date first for logging purposes
        self.current_date = get_datetime()

        if not self.fetch_history(context, data):
            return

        #  Filter minute frequency
        self._check_minute_freq(context, data)

        if self.in_job:
            job = get_current_job()
            job.meta["date"] = str(self.current_date)
            job.save_meta()

        self.log.debug("Processing algo iteration")
        for i in context.blotter.open_orders:
            msg = "Canceling unfilled open order {}".format(i)
            self.log.info(msg)
            self.notify(msg)
            cancel_order(i)

        if not self.fetch_history(context, data):
            return

        self._filter_fetched_history(context, data)

        # ## enqueue ml models as soon as data filtered
        if self._ml_models:
            self._enqueue_ml_calcs(context, data)

        else:
            for dataset, manager in self._datasets.items():
                manager.calculate(context)
                manager.record_data(context)

        for i in self._market_indicators:
            try:
                i.calculate(self.state.prices)
                i.record()
            except Exception as e:
                self.log.error(e)
                self.log.error("Error calculating {}, skipping...".format(i.name))

        for i in self._ml_models:
            i.record()

        self._extra_handle(context, data)
        self._count_signals(context, data)

        if context.frame_stats:
            pretty_output = stats_utils.get_pretty_stats(context.frame_stats)
            self.log.notice(pretty_output)
            if not self.is_backtest:
                outputs.save_stats_to_storage(self)
        self.state.dump_to_context(context)

    @property
    def total_plots(self):
        dataset_inds = 0
        for d, m in self._datasets.items():
            dataset_inds += len(m._indicators)

        return len(self._market_indicators) + len(self._datasets) + dataset_inds + self._extra_plots

    def _get_last_date(self, context, data):
        """Get last date filtered to work in the train dataset.
        """
        if self.last_date is None:

            # self.state.prices was set in fetch_history

            #  Filter selected dates
            filter_dates = pd.date_range(
                start=self.date_init_reference,
                end=self.state.prices.iloc[-1].name,
                freq=str(self.state.MINUTE_FREQ) + "min",
            )

            self.state.prices = self.state.prices.loc[filter_dates]

            return self.state.prices.iloc[-1].name

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

        strat_dir = os.path.join(os.path.abspath(PERF_DIR), self.name)
        os.makedirs(strat_dir, exist_ok=True)
        plot_file = f"summary_plot.png"
        filename = os.path.join(strat_dir, plot_file)
        plt.savefig(filename)
        plt.close()

        outputs.save_plot_to_storage(self, filename)
        

    def _analyze(self, context, results):
        """Plots results of algo performance, external data, and indicators"""
        self.log.warning("Calling analyze function and completing algorithm")
        ending_cash = results.cash[-1]
        self.log.notice("Ending cash: ${}".format(ending_cash))
        self.log.notice("Completed for {} trading periods".format(self.state.i))
        self.notify(f"Your strategy {self.name} has completed. You're ending cash is {ending_cash}")

        try:
            self._make_plots(context, results)
            # TODO - fix KeyError in quant analysis
            # quant.dump_plots_to_file(self.name, results)
            self.quant_results = quant.dump_summary_table(self.name, self.trading_info, results)

            extra_results = self.get_extra_results(context, results)

            for i in self._ml_models:
                i.analyze(self.name, self.state.DATA_FREQ, extra_results)

        except (ValueError, ZeroDivisionError, KeyError):
            self.log.warning("Not enough data to make plots")

        # need to catch all exceptions because algo will end either way
        except Exception as e:
            self.log.error("Error during shutdown/analyze()")

        try:
            outputs.save_analysis_to_storage(self, results)
        except Exception:
            self.log.error("Failed to upload strat analysis to storage", exec_info=True)

        self.state.dump_to_context(context)

    # def upload_results(self, context, results):

    def get_extra_results(self, context, results):
        extra_results = {
            "start": self.state.START,
            "end": self.state.END,
            "minute_freq": self.state.MINUTE_FREQ,
            "data_freq": self.state.DATA_FREQ,
            "return_profit_pct": results.algorithm_period_return.tail(1).values[0],
            "sharpe_ratio": "",
            "sharpe_ratio_benchmark": "",
            "sortino_ratio": "",
            "sortino_ratio_benchmark": "",
        }

        if self.state.DATA_FREQ == "minute":
            try:
                self.filter_dates = self.filter_dates.append(results.algorithm_period_return.tail(1).index)
                if results.algorithm_period_return.loc[self.filter_dates].dropna().std() != 0.0:
                    extra_results['sharpe_ratio'] = results.algorithm_period_return.loc[self.filter_dates].dropna().mean() / results.algorithm_period_return.loc[self.filter_dates].dropna().std()
                if (results.algorithm_period_return.loc[self.filter_dates].dropna() - results.benchmark_period_return.loc[self.filter_dates].dropna()).std() != 0.0:
                    extra_results['sharpe_ratio_benchmark'] = (results.algorithm_period_return.loc[self.filter_dates].dropna() - results.benchmark_period_return.loc[self.filter_dates].dropna()).mean() / (results.algorithm_period_return.loc[self.filter_dates].dropna() - results.benchmark_period_return.loc[self.filter_dates].dropna()).std()
                if self.filter_dates in results.algorithm_period_return.loc[results.algorithm_period_return < 0].index:
                    extra_results['sortino_ratio'] = results.algorithm_period_return.loc[self.filter_dates].dropna().mean() / np.sqrt((results.algorithm_period_return.loc[results.algorithm_period_return < 0].loc[self.filter_dates].dropna() ** 2).mean())
                    extra_results['sortino_ratio_benchmark'] = (results.algorithm_period_return.loc[self.filter_dates].dropna() - results.benchmark_period_return.loc[self.filter_dates].dropna()).mean() / np.sqrt((results.algorithm_period_return.loc[results.algorithm_period_return < 0].loc[self.filter_dates].dropna() ** 2).mean())
            except:
                pass
        else:
            extra_results["sharpe_ratio"] = results.sharpe[30:].mean()
            extra_results["sortino_ratio"] = results.sortino[30:].mean()

        return extra_results

    def add_market_indicator(self, indicator, priority=0, **params):
        """Registers an indicator to be applied to standard OHLCV exchange data"""
        if isinstance(indicator, str):
            indicator = technical.get_indicator(indicator, **params)

        # TODO: allow other assets for indicators
        indicator.symbol = self.trading_info["ASSET"]

        # if "symbol" not in params:
        #     params["symbol"] = self.trading_info["ASSET"]
        #     self.log.debug(f'Setting new indicator symbol as {self.trading_info["ASSET"]}')
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

        indicator.symbol = self.trading_info["ASSET"]

        # indic

        # if "symbol" not in params:
        #     params["symbol"] = self.trading_info["ASSET"]
        #     self.log.debug(f'Setting new indicator symbol as {self.trading_info["ASSET"]}')
        self._ml_models.append(indicator)

    def use_dataset(self, dataset_name, columns):
        """Registers an external dataset to be integrated into algo"""
        if self._ml_models:
            # Using from CONFIG.START date - CONFIG.BARS days to CONFIG.END date
            config = copy.deepcopy(self.trading_info)
            config["START"] = (
                datetime.datetime.strptime(config["START"], "%Y-%m-%d")
                + datetime.timedelta(days=-config["BARS"])
            ).strftime("%Y-%m-%d")
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
            elif "." in sig_params[arg]:
                [indicator_label, output] = sig_params[arg].split(".")
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
        func = getattr(signal_utils, obj["func"])
        params = obj.get("params", {})

        kwargs = self._get_kw_from_signal_params(params, func)
        self.log.debug("Calculating {}".format(func.__name__))
        return func(**kwargs)

    def _calculate_custom_signals(self, context, data):
        sells, buys, neutrals = 0, 0, 0
        for i in self._buy_signal_objs:
            if self._construct_signal(i):
                buys += 1
                self.log.debug("Custom Signal: BUY")
            else:
                neutrals += 1

        for i in self._sell_signal_objs:
            if self._construct_signal(i):
                sells += 1
                self.log.debug("Custom Signal: SELL")
            else:
                neutrals += 1

        return sells, buys, neutrals

    def _count_signals(self, context, data):
        """Processes indicator to determine buy/sell opportunities"""

        sells, buys, neutrals = self._calculate_custom_signals(context, data)

        for f in self._signal_buy_funcs:
            if f(context, data):
                buys += 1
            else:
                neutrals += 1

        for f in self._signal_sell_funcs:
            if f(context, data):
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
            msg = "Signaling to buy"
            self.log.notice(msg)
            self.notify(msg)
            self.make_buy(context)

        elif sells > buys:
            msg = "Signaling to sell"
            self.log.notice(msg)
            self.notify(msg)
            self.make_sell(context)

    def make_buy(self, context):
        if context.portfolio.cash < self.state.price * self.state.ORDER_SIZE:
            self.log.warn(
                "Skipping signaled buy due to cash amount: {} < {}".format(
                    context.portfolio.cash, (self.state.price * self.state.ORDER_SIZE)
                )
            )

            msg = """
            A signaled buy order was cancelled, because you don't have enough cash for the order.\n
            Consider adding more cash to your account or adjusting your order size
            """
            self.notify(dedent(msg))
            return

        self.log.notice("Making Buy Order")
        if self._buy_func is None:
            return self._default_buy(context)

        self._buy_func(context)

    def make_sell(self, context):
        if self.state.asset not in context.portfolio.positions:
            self.log.warn("Skipping signaled sell due b/c no position")
            msg = """\
            A signaled sell order was cancelled, because you currently have no posiiton.\n
            """
            self.notify(dedent(msg))
            return

        self.log.notice("Making Sell Order")
        if self._sell_func is None:
            return self._default_sell(context)

        self._sell_func(context)

    def check_open_positions(self, context):
        """Check open positions to sell to take profit or to stop loss.
        """
        if self.state.asset in context.portfolio.positions:
            position = context.portfolio.positions.get(self.state.asset)
            # self.log.info('Checking open positions: {amount} positions with cost basis {cost_basis}'.format(amount=position.amount, cost_basis=position.cost_basis))

            if self.state.price >= position.cost_basis * (1 + TAKE_PROFIT):  #  Take Profit
                self._take_profit_sell(context, position)

            if self.state.price < position.cost_basis * (1 - STOP_LOSS):  # Stop Loss
                self._stop_loss_sell(context, position)

    def _take_profit_sell(self, context, position):
        order(
            asset=self.state.asset,
            amount=-position.amount,
            limit_price=self.state.price * (1 - self.state.SLIPPAGE_ALLOWED),
        )

        profit = (self.state.price * position.amount) - (position.cost_basis * position.amount)

        msg = "Sold {amount} @ {price} Profit: {profit}; Produced by take-profit signal".format(
            amount=position.amount, price=self.state.price, profit=profit, date=get_datetime()
        )

        self.log.notice(msg)
        self.notify(dedent(msg))

    def _stop_loss_sell(self, context, position):
        order(
            asset=self.state.asset,
            amount=-position.amount,
            # limit_price=self.state.price * (1 - self.state.SLIPPAGE_ALLOWED),
        )

        profit = (self.state.price * position.amount) - (position.cost_basis * position.amount)

        msg = "Sold {amount} @ {price} Profit: {profit}; Produced by stop-loss signal at {date}".format(
            amount=position.amount, price=self.state.price, profit=profit, date=get_datetime()
        )

        self.log.notice(msg)
        self.notify(dedent(msg))

    def _default_buy(self, context, size=None, price=None, slippage=None):
        position = context.portfolio.positions.get(self.state.asset)
        if position is None:
            self.log.info("Using default buy function")
            order(
                asset=self.state.asset,
                amount=self.state.ORDER_SIZE,
                limit_price=self.state.price * (1 + self.state.SLIPPAGE_ALLOWED),
            )
            msg = "Bought {amount} @ {price}".format(
                amount=self.state.ORDER_SIZE, price=self.state.price
            )
            self.log.notice(msg)
            self.notify(msg)
        else:
            msg = "Skipping signaled buy due to open position: {amount} positions with cost basis {cost_basis}".format(
                amount=position.amount, cost_basis=position.cost_basis
            )
            self.log.warn(msg)
            self.notify(msg)

    def _default_sell(self, context, size=None, price=None, slippage=None):
        self.log.info("Using default sell function")
        position = context.portfolio.positions.get(self.state.asset)
        if position == 0:
            self.log.warn("Position Zero, skipping sell")
            return

        # Cost Basis
        cost_basis = position.cost_basis
        self.log.notice(
            "Holdings: {amount} @ {cost_basis}".format(
                amount=position.amount, cost_basis=cost_basis
            )
        )
        # Sell when holding and got sell singnal
        profit = (self.state.price * position.amount) - (cost_basis * position.amount)
        order_target_percent(
            asset=self.state.asset,
            target=0,
            limit_price=self.state.price * (1 - self.state.SLIPPAGE_ALLOWED),
        )
        msg = "Sold {amount} @ {price} Profit: {profit}".format(
            amount=position.amount, price=self.state.price, profit=profit
        )
        self.log.notice(msg)
        self.notify(msg)

    # Save the prices and analysis to send to analyze

    def run(self, live=False, simulate_orders=True, user_id=None, viz=True, as_job=False):
        """Executes the trade strategy as a catalyst algorithm

        Basic algorithm behavior is defined cia the config object, while
        iterative logic is managed by the Strategy object.
        """
        self.in_job = as_job
        self.viz = viz

        if self.in_job:
            job = get_current_job()
            job.meta["config"] = self.to_dict()
            job.meta["telegram_id"] = self.telegram_id
            job.save_meta()

        self._live = live or self.trading_info.get("LIVE", False)
        self._simulate_orders = simulate_orders
        self.user_id = user_id

        if self.is_backtest:
            return self.run_backtest()

        elif self.is_paper:
            return self.run_paper()

        elif self.is_live:
            return self.run_live(user_id)

    def run_backtest(self):
        self.log.notice("Running in backtest mode")
        try:
            run_algorithm(
                algo_namespace=self.id,
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
        except exchange_errors.PricingDataNotLoadedError as e:
            self.log.critical("Failed to run stratey Requires data ingestion")
            raise e
            # from kryptos.worker import ingester
            # ingester.run_ingest(self.exchange, symbol=self.trading_info['ASSET'])
            # load.ingest_exchange(self.trading_info)
            # self.log.warn("Exchange ingested, please run the command again")
            # self.run(live, simulate_orders, viz, as_job)

    def run_paper(self):
        self.log.notice("Running in paper mode")
        self._live = True
        self._simulate_orders = True
        self._run_real_time(simulate_orders=True)

    def run_live(self, user_id):
        from google.api_core.exceptions import NotFound

        self._live = True
        self._simulate_orders = False
        self.log.notice("Running in live mode")
        if user_id is None:
            raise ValueError("user_id is required for auth when running in live mode")
        self.user_id = user_id

        try:
            auth_alias = auth.get_user_auth_alias(self.user_id, self.exchange.lower())
        except NotFound:
            self.log.error("Missing user exchange auth")
            self.notify(
                "Before running a live strategy, you will need to authorize with your API key"
            )
            return pd.DataFrame()

        if auth_alias is None:
            self.log.error("Aborting strategy due to missing exchange auth")
            return pd.DataFrame()

        try:
            self._run_real_time(simulate_orders=False, user_id=user_id, auth_aliases=auth_alias)
        except exchange_errors.ExchangeAuthEmpty:
            self.log.critical("Failed to run strategy due to missing exchange auth")
            self.notify(
                "Failed to run strategy due to missing exchange auth. If you have already provided your API key please re-authenticate to ensure the correct key is correct"
            )
            return pd.DataFrame()

        except exchange_errors.NotEnoughCashError as e:
            self.log.critical(str(e))
            self.notify(
                f"You do not have enough cash on the exchange account to run the strategy.\n\n{str(e)}"
            )
            return pd.DataFrame()

        finally:
            auth.delete_alias_file(self.user_id, self.exchange)

    def _run_real_time(self, simulate_orders=True, user_id=None, auth_aliases=None):
        self.log.notice("Running live trading, simulating orders: {}".format(simulate_orders))
        if self.trading_info["DATA_FREQ"] != "minute":
            self.log.warn('"daily" data frequency is not supported in live mode, using "minute"')
            self.trading_info["DATA_FREQ"] = "minute"

        # start = arrow.get(self.trading_info["START"], 'YYYY-M-D')
        end = arrow.get(self.trading_info["END"])

        if end < arrow.utcnow().floor("minute"):
            self.log.warning(f'End Date: {end} is invalid, will use ')
            # self.log.warning("Specified end date is invalid, will use 3 days from today")
            self.log.warning("Will use 30 minutes from now")
            end = arrow.utcnow().shift(minutes=+30)
            self.trading_info["END"] = end.format("YYYY-M-D-H-MM")

        # self.log.notice(f'Starting Strategy {start.humanize()} -- {start}')
        self.log.notice(f"Stopping strategy {end.humanize()} -- {end}")

        # catalyst loads state before init called
        # so need to fetch state before algorithm starts
        if outputs.load_state_from_storage(self):
            self.log.info(f'Resuming strategy with saved state')

        run_algorithm(
            capital_base=self.trading_info["CAPITAL_BASE"],
            initialize=self._init_func,
            handle_data=self._process_data,
            analyze=self._analyze,
            exchange_name=self.trading_info["EXCHANGE"],
            live=True,
            algo_namespace=self.id,
            quote_currency=self.trading_info["BASE_CURRENCY"],
            live_graph=False,
            simulate_orders=simulate_orders,
            stats_output=None,
            # start=pd.to_datetime(start.datetime, utc=True),
            end=pd.to_datetime(end.datetime, utc=True),
            auth_aliases=auth_aliases,
        )
