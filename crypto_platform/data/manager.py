import os
import csv
import pandas as pd
import matplotlib.pyplot as plt

from catalyst.api import record
from pytrends.request import TrendReq
import quandl

from crypto_platform.config import CONFIG
from crypto_platform.data import csv_data
from crypto_platform.data.clients import quandl_client
from crypto_platform.utils import viz
from crypto_platform.strategy.indicators import basic

from logbook import Logger

DATA_DIR = os.path.dirname(os.path.abspath(csv_data.__file__))

AVAILABLE_DATASETS = [
    'google',
    'quandl',
]


def get_data_manager(name):
    datasets = {
        'google': GoogleTrendDataManager,
        'quandl': QuandleDataManager,
    }
    return datasets.get(name, DataManager)


class DataManager(object):
    def __init__(self, name, columns=None):
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
        index = pd.date_range(start=CONFIG.START, end=CONFIG.END)
        self.df = pd.DataFrame(index=index)

        self._indicator_map = {}

        self.log = Logger(name)

    def fetch_data(self):
        pass

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

    def attach_indicator(self, indicator, cols=None):
        """Declares an indicator to be calculated for the given columns

        Any registered indicators are applied to their respective columns
        at each iteration of the algorithm.
        This method can be called before or during algo execution.

        Arguments:
            indicator {str}

        Keyword Arguments:
            cols {list} -- Names of target columns (default: all columns)
        """
        if cols is None:
            cols = self.columns

        if indicator not in self._indicator_map:
            self._indicator_map[indicator] = []

        self._indicator_map[indicator].extend(cols)

    def calculate(self, context):
        """Calls for calculation of indicators currently registered with the DataManager

        This method is called by a Strategy object at every algo iteration.
        The outputs and calculation for each indicator is handled and stored by
        the underlying Indicator objects.

        Arguments:
            context {pd.Dataframe} -- Catalyst peristent algo context object
        """
        date = context.blotter.current_dt.date()
        for i, cols in self._indicator_map.items():

            indic_obj = getattr(basic, i.upper())()

            # Assuming only use of basic indicators for now
            # Basic indicators accept a series as opposed to a df with technical indicators
            for c in cols:
                col_vals = self.df_to_date(date)[c]
                indic_obj.calculate(col_vals)
                indic_obj.record()

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
            return record_payload

        for k in self.columns:
            current_val = self.column_by_date(k, date)
            record_payload[k] = current_val

        record(**record_payload)
        return record_payload

    def plot(self, results, pos):
        """Calls for plotting of recored external data and registered indicators

        This method is called by a Strategy object once after algo execution has finished.
        The plotting each indicator is handled by the underlying Indicator objects.

        Arguments:
            results {pandas.Dataframe} -- Catalyst algo results of all recored data
            pos {int} -- 3 digit integer used to represent matplotlib subplot position (ex. 212)
        """
        for col in self.columns:
            ax = viz.plot_column(results, col, pos, label=col, y_label=self.name)

        for i in self._indicator_map:
            indic_obj = getattr(basic, i.upper())()
            indic_obj.plot(results, pos, twin=ax)
        plt.legend()


class GoogleTrendDataManager(DataManager):

    def __init__(self, columns):
        super(GoogleTrendDataManager, self).__init__('GoogleTrends', columns=columns)
        """DataManager object used to fetch and integrate Google Trends data"""

        self.trends = TrendReq(hl='en-US', tz=360)
        timeframe = str(CONFIG.START.date()) + ' ' + str(CONFIG.END.date())

        self.trends.build_payload(self.columns, cat=0, timeframe=timeframe, geo='', gprop='')
        df = self.trends.interest_over_time()
        df.index = pd.to_datetime(df.index, unit='s')
        self.df = df


class QuandleDataManager(DataManager):
    def __init__(self, columns):
        super(QuandleDataManager, self).__init__('QuandlData', columns=columns)
        """DataManager object used to fetch and integrate Quandl Blockchain database"""

        _api_key = os.getenv('QUANDL_API_KEY')
        quandl.ApiConfig.api_key = _api_key
        self.data_dir = os.path.join(DATA_DIR, 'quandle', )

        df = pd.read_csv(self.csv, index_col=[0])
        df.index = pd.to_datetime(df.index)
        self.df = df

        self.pretty_names = {}
        self._build_name_map()

    @property
    def csv(self):
        """Path of quandl csv file"""
        f = quandl_client.data_csv()
        if not os.path.exists(f):
            self.log.info('Quandle Data not downloaded, fetching...')
            quandl_client.fetch_all()
        return f

    def _build_name_map(self):
        with open(quandl_client.code_csv(), 'r') as f:
            for i in csv.reader(f):
                col_name = i[0].replace('BCHAIN/', '')
                self.pretty_names[col_name] = i[1]

    def pretty_title(self, col):
        return self.pretty_names[col]
