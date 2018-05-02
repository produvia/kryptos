import os
import csv
import json
import datetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import logbook
from catalyst.api import record
from pytrends.request import TrendReq
import quandl

# from crypto_platform.config import self.config
from crypto_platform.data import csv_data
from crypto_platform.data.clients import quandl_client
from crypto_platform.utils import viz
from crypto_platform.strategy.indicators import basic, technical
from crypto_platform.strategy import DEFAULT_CONFIG
from crypto_platform import logger_group
#from crypto_platform import errors

from logbook import Logger


DATA_DIR = os.path.dirname(os.path.abspath(csv_data.__file__))

AVAILABLE_DATASETS = ["google", "quandl"]


def get_data_manager(name, cols=None, config=None):
    datasets = {"google": GoogleTrendDataManager, "quandl": QuandleDataManager}
    try:
        return datasets[name](columns=cols, config=config)

    except KeyError as e:
        raise e(
            "No dataset available with name {}.\nAvailable Datasets: {}".format(
                name, AVAILABLE_DATASETS
            )
        )


class DataManagerLogger(logbook.Logger):

    def __init__(self, manager):
        self.manager = manager
        super().__init__(name=self.manager.name.upper())

    def process_record(self, record):
        logbook.Logger.process_record(self, record)
        record.extra["trade_date"] = self.manager.current_date


class DataManager(object):

    def __init__(self, name, columns=None, config=None):
        """Base class of Data Managers

        Data Managers are responsible for all operations related to
        to external datasets, including fetching and visualizing.

        These objects are utilized by Strategy objects during algroithm execution to access
        and integrate external data into algorithm logic.

        The following three methods are to be called during algo execution
        and utilize Catalyst's context object

        `calculate` - calculates registered indicators every iteration
        `record_data` - records external data and indicators every iteration
        `plot` - plots data and indicators after algo execution

        Arguments:
            name {str} -- name of the dataset

        Keyword Arguments:
            columns {list} -- The target columns to analyzed (default: {None})
        """

        self.name = name
        self.columns = columns or []

        if config is None:
            config = DEFAULT_CONFIG

        self.START = pd.to_datetime(config["START"], utc=True)
        self.END = pd.to_datetime(config["END"], utc=True)

        index = pd.date_range(start=self.START, end=self.END)
        self.df = pd.DataFrame(index=index)

        self._indicators = []
        self._indicator_map = {}

        self.current_date = None
        self.log = DataManagerLogger(self)
        logger_group.add_logger(self.log)

    def fetch_data(self):
        pass

    def serialize(self):
        return {
            "name": self.name,
            "columns": self.columns,
            "indicators": [i.serialize() for i in self._indicators],
        }

    def current_data(self, date):
        """Grabs datset info for the provided data

        Arguments:
            date {pandas.tslib.Timestamp}

        Returns:
            pandas.Dataframe
        """
        return self.df.loc[date]

    def column_by_date(self, col, date):
        series = self.df.loc[date]
        return series.get(col)

    def df_to_date(self, date):
        sliced_df = self.df[:date]
        return sliced_df

    def attach_indicator(self, indicator, col=None):
        """Declares an indicator to be calculated for the given columns

        Any registered indicators are applied to their respective columns
        at each iteration of the algorithm.
        This method can be called before or during algo execution.

        Arguments:
            indicator {str}

        Keyword Arguments:
            cols {list} -- Names of target columns (default: all columns)
        """
        if col is None:
            col = self.columns

        if indicator not in self._indicators:
            try:
                ind_obj = basic.get_indicator(indicator, symbol=col, dataset=self.name)
            except LookupError:
                ind_obj = technical.get_indicator(indicator, symbol=col, dataset=self.name)
            # ind_obj = getattr(basic, indicator.upper())(dataset=self.name)
            self._indicators.append(ind_obj)

        if indicator not in self._indicator_map:
            self._indicator_map[indicator.upper()] = []

        self._indicator_map[ind_obj.name].append(col)

    def calculate(self, context):
        """Calls for calculation of indicators currently registered with the DataManager

        This method is called by a Strategy object at every algo iteration.
        The outputs and calculation for each indicator is handled and stored by
        the underlying Indicator objects.

        Arguments:
            context {pd.Dataframe} -- Catalyst peristent algo context object
        """
        self.current_date = context.blotter.current_dt.date()

        # Assuming only use of basic indicators for now
        # Basic indicators accept a series as opposed to a df with technical indicators
        for i in self._indicators:
            for col in self._indicator_map[i.name]:
                self.log.debug("Calculating {} for {}".format(i.name, col))
                try:
                    col_vals = self.df_to_date(self.current_date)[col]
                    i.calculate(col_vals)
                    i.record()
                except KeyError:
                    msg = """{} is set as the column for {}, but it is not found in the dataset.
                    Does the config look right?:
                    {}
                        """.format(
                        col, i.name, json.dumps(self.serialize(), indent=2)
                    )
                    e = Exception(msg)
                    self.log.exception(e)
                    raise e

    def record_data(self, context):
        """Records external data for the current algo iteration

        Data from the external dataset is recorded to Catalyst's
        persistant context object along with market data

        Arguments:
            context {pd.Dataframe} --  Catalyst peristent algo context object

        Returns:
            dict -- Dict of column keys and data recored to catalyst
        """
        date = context.blotter.current_dt.date()
        record_payload = {}

        if date not in self.df.index:
            raise ValueError("No {} data found for {}".format(self.name, date))

        for k in self.columns:
            current_val = self.column_by_date(k, date)
            # TODO: some dates are doubled due to smaller date steps
            if isinstance(current_val, pd.Series):
                current_val = current_val.mean()
            record_payload[k] = current_val

        self.log.debug("Recording {}".format(record_payload))
        record(**record_payload)
        return record_payload

    def plot(self, results, pos, skip_indicators=False, **kw):
        """Calls for plotting of recored external data and registered indicators

        This method is called by a Strategy object once after algo execution has finished.
        The plotting each indicator is handled by the underlying Indicator objects.

        Arguments:
            results {pandas.Dataframe} -- Catalyst algo results of all recored data
            pos {int} -- 3 digit integer used to represent matplotlib subplot position (ex. 212)
        """
        for col in self.columns:
            ax = viz.plot_column(results, col, pos, label=col, y_label=self.name, **kw)

        if not skip_indicators:
            self.plot_dataset_indicators(results, pos)
        plt.legend()

    def plot_dataset_indicators(self, results, pos, **kw):
        for i in self._indicators:
            i.plot(results, pos, **kw)
        plt.legend()


class GoogleTrendDataManager(DataManager):

    def __init__(self, columns, config=None):
        super(GoogleTrendDataManager, self).__init__("google", columns, config)
        """DataManager object used to fetch and integrate Google Trends data"""

        self.trends = TrendReq(hl="en-US", tz=360)
        self.df = pd.DataFrame()

    def date_steps(self):
        dates = []
        start, end = self.START.date(), self.END.date()

        if start + relativedelta(weeks=+1) >= end:
            self.log.debug("Using daily steps for {} - {}".format(start, end))
            dates = [dt for dt in rrule(freq=DAILY, interval=1, dtstart=start, until=end)]

        elif start + relativedelta(months=+6) >= end:
            self.log.debug("Using weekly steps for {} - {}".format(start, end))
            dates = [dt for dt in rrule(freq=WEEKLY, interval=1, dtstart=start, until=end)]

        elif start + relativedelta(months=+6) >= end:
            self.log.debug("Using monthly steps for {} - {}".format(start, end))
            dates = [dt for dt in rrule(freq=MONTHLY, interval=1, dtstart=start, until=end)]

        else:
            dates = [dt for dt in rrule(freq=MONTHLY, interval=6, dtstart=start, until=end)]
            self.log.debug("Using 6 month steps for {} - {}".format(start, end))

        last_date = dates[-1].date()
        if last_date < end:
            dates.append(self.END)

        # TODO: Determine best method of normalizing trend values for daily data
        # while last_date + relativedelta(months=+1) < end:
        #     self.log.debug('Building remainer MONTH steps')
        #     final_steps = [dt for dt in rrule(freq=MONTHLY, interval=1, dtstart=dates[-1], until=end) if dt not in dates]
        #     dates.extend(final_steps)
        #     last_date = dates[-1].date()

        # while last_date + relativedelta(weeks=+1) < end:
        #     self.log.debug('Building remainer WEEKLY steps')

        #     final_steps = [dt for dt in rrule(freq=WEEKLY, interval=1, dtstart=dates[-1], until=end) if dt not in dates]
        #     dates.extend(final_steps)
        #     last_date = dates[-1].date()

        # while last_date + relativedelta(days=+1) < end:
        #     self.log.debug('Building remainer DAILY steps')

        #     final_steps = [dt for dt in rrule(freq=DAILY, interval=1, dtstart=dates[-1], until=end) if dt not in dates]
        #     dates.extend(final_steps)
        #     last_date = dates[-1].date()

        return dates

    @property
    def datetime_pairs(self):
        date_pairs = []
        steps = self.date_steps()
        for i, date in enumerate(steps):
            if i < len(steps) - 1:
                date_pairs.append((date, steps[i + 1]))
        self.log.debug("Date Pairs: {}".format(date_pairs))
        return date_pairs

    @property
    def timeframes(self):
        timeframes = []
        for pair in self.datetime_pairs:
            as_str = str(pair[0].date()) + " " + str(pair[1].date())
            timeframes.append(as_str)
        return timeframes

    def fetch_data(self):
        self.log.warn(
            """
            The GoogleTrend Dataset is not yet reliable for obtaining daily data over large timespans.
            This may result in innacurate peaks in trend volume
            """
        )
        trend_data = []
        for i, t in enumerate(self.timeframes):
            self.log.info("Fetching trend data for {}".format(t))
            self.trends.build_payload(self.columns, cat=0, timeframe=t, geo="", gprop="")
            d = self.trends.interest_over_time()

            if d.empty:
                self.log.warn(
                    "No Trend Data for {} on {}\n Filling with blank data".format(self.columns, t)
                )
                date_pair = self.datetime_pairs[i]
                delta = date_pair[1].date() - date_pair[0].date()
                empty_data = [0] * (delta.days + 1)
                d = pd.DataFrame(index=pd.date_range(date_pair[0].date(), date_pair[1].date()))
                for c in self.columns:
                    d[c] = empty_data

            self.log.debug("Retrieved {} days of trend data".format(len(d)))
            trend_data.append(d)

        self.df = self.normalize_data(trend_data)

    def normalize_data(self, trend_data):
        df = pd.DataFrame(index=pd.date_range(self.START, self.END))
        if len(trend_data) == 0:
            self.log.critical("No trend data found for {}".format(self.columns))
            raise ValueError("No trend data to normalize")

        # https://github.com/anyuzx/bitcoin-google-trend-strategy/blob/master/bitcoin_google_trend_strategy.py
        renorm_factor = 1.0
        for c in self.columns:
            last_entry = 0
            trend_array = []
            for i, frame in enumerate(trend_data[::-1]):
                if frame.empty:
                    self.log.critical(
                        "Trend Dataframe empty for {}: {}-{}".format(
                            c, self.START.date(), self.END.date()
                        )
                    )
                    raise ValueError("Incomplete trend data, can't normalize")

                if i == 0:
                    trend_array = list(frame[c].values)
                    last_entry = frame[c].values[-1]

                elif all([v == 0 for v in frame[c].values]):
                    self.log.debug("Skipping normalization for all 0 dataframe")
                    trend_array.extend(list(frame[c][1:]))
                    last_entry = frame[c].values[-1]

                else:
                    first_entry = [i for i in frame[c].values if i != 0][0]
                    renorm_factor *= float(last_entry) / float(first_entry)
                    renorm_array = frame[c].values * renorm_factor
                    trend_array.extend(list(renorm_array[1:]))
                    last_entry = frame[c].values[-1]

            try:
                trend_array = np.array(trend_array)
                trend_array = 100.0 * trend_array / trend_array.max()
                df[c] = trend_array
            except RuntimeWarning as e:
                raise e

        return df


class QuandleDataManager(DataManager):

    def __init__(self, columns, config=None):
        super(QuandleDataManager, self).__init__("quandl", columns, config)
        """DataManager object used to fetch and integrate Quandl Blockchain database"""

        self.config = config
        _api_key = os.getenv("QUANDL_API_KEY")
        quandl.ApiConfig.api_key = _api_key
        self.data_dir = os.path.join(DATA_DIR, "quandle")

    def fetch_data(self):
        df = pd.read_csv(self.csv, index_col=[0])

        df_start, df_end = pd.to_datetime(df.iloc[0].name), pd.to_datetime(df.iloc[-1].name)
        algo_start, algo_end = pd.to_datetime(self.config["START"]), pd.to_datetime(
            self.config["END"]
        )

        if algo_start < df_start or algo_end > df_end:
            self.log.warn("Fetching missing quandl data")
            quandl_client.fetch_all()

        df.index = pd.date_range(start=df.iloc[0].name, end=df.iloc[-1].name, freq="D")
        self.df = df

        self.pretty_names = {}
        self._build_name_map()

    @property
    def csv(self):
        """Path of quandl csv file"""
        f = quandl_client.data_csv()
        if not os.path.exists(f):
            self.log.warn("Quandle Data not downloaded, fetching...")
            quandl_client.fetch_all()
        return f

    def _build_name_map(self):
        with open(quandl_client.code_csv(), "r") as f:
            for i in csv.reader(f):
                col_name = i[0].replace("BCHAIN/", "")
                self.pretty_names[col_name] = i[1]

    def pretty_title(self, col):
        return self.pretty_names[col]
