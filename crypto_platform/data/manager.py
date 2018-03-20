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

from logbook import Logger

DATA_DIR = os.path.dirname(os.path.abspath(csv_data.__file__))


def get_data_manager(name):
    datasets = {
        'google': GoogleTrendDataManager,
        'quandl': QuandleDataManager,
    }
    return datasets.get(name, DataManager)


class DataManager(object):
    def __init__(self, name, columns=None):

        self.name = name
        self.columns = columns or []
        index = pd.date_range(start=CONFIG.START, end=CONFIG.END)
        self.df = pd.DataFrame(index=index)

        self.log = Logger(name)

    def fetch_data(self):
        pass

    def current_data(self, date):
        return self.df.loc[date]

    def column_by_date(self, col, date):
        series = self.df.loc[date]
        return series.get(col)

    def record_data(self, context, data):
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
        for col in self.columns:
            viz.plot_metric(results, col, pos, label=col, y_label=self.name)
        plt.legend()


class GoogleTrendDataManager(DataManager):

    def __init__(self, columns):
        super(GoogleTrendDataManager, self).__init__('GoogleTrends', columns=columns)

        self.trends = TrendReq(hl='en-US', tz=360)
        timeframe = str(CONFIG.START.date()) + ' ' + str(CONFIG.END.date())

        self.trends.build_payload(self.columns, cat=0, timeframe=timeframe, geo='', gprop='')
        df = self.trends.interest_over_time()
        df.index = pd.to_datetime(df.index, unit='s')
        self.df = df


class QuandleDataManager(DataManager):
    def __init__(self, columns):
        super(QuandleDataManager, self).__init__('QuandlData', columns=columns)

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
