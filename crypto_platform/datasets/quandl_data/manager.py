import os
import csv
import pandas as pd
from catalyst.api import record
from crypto_platform.datasets.quandl_data import client

from logbook import Logger

log = Logger('QuandleDataManager')


class QuandleDataManager(object):
    """docstring for QuandleDataManager"""

    def __init__(self):

        df = pd.read_csv(self.csv, index_col=[0])
        df.index = pd.to_datetime(df.index)
        self.df = df

        self.pretty_names = {}
        self._build_name_map()

    @property
    def csv(self):
        f = client.data_csv()
        if not os.path.exists(f):
            log.info('Quandle Data not downloaded, fetching...')
            client.fetch_all()
        return f

    def _build_name_map(self):
        with open(client.code_csv(), 'r') as f:
            for i in csv.reader(f):
                col_name = i[0].replace('BCHAIN/', '')
                self.pretty_names[col_name] = i[1]

    def current_data(self, date):
        return self.df.loc[date]

    def column_by_date(self, col, date):
        series = self.df.loc[date]
        return series.get(col)

    def pretty_title(self, col):
        return self.pretty_names[col]

    def record_data(self, context, data, datasets):
        date = context.blotter.current_dt.date()
        record_payload = {}

        if date not in self.df.index:
            return record_payload

        for col in datasets:
            current_val = self.column_by_date(col, date)
            record_payload[col] = current_val
            log.info('{}: {}'.format(col, current_val))

        record(**record_payload)



