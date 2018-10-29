from catalyst.api import get_datetime, record
import pandas as pd
from rq import Queue
import time

from kryptos.utils import tasks
from kryptos.strategy.indicators import AbstractIndicator


def get_indicator(name, **kw):
    subclass = globals().get(name.upper())
    if subclass is not None:
        return subclass(**kw)

    return MLIndicator(name, **kw)


class MLIndicator(AbstractIndicator):

    def __init__(self, name, **kw):
        super().__init__(name, **kw)
        """Factory for creating an indicator using the machine learning models

        The costructor is passed the name of the indicator.
        The calculation is performed at each iteration and is recored
        and plotted based on a ML model function's outputs.

        To signal trade opportunities, subclassed objects can implement
        the signals_buy and signals_sell methods.
        """
        self.hyper_params = None
        self.first_iteration = True
        self.current_date = None
        self.current_job_id = None
        # buy/sell are set as attributes rather than calculated properties for ML
        # because the results are returned from the worker processes
        # in which the MLIndicator instance is not available
        self._signals_buy = False
        self._signals_sell = False

    @property
    def signals_buy(self):
        return self._signals_buy

    @property
    def signals_sell(self):
        return self._signals_buy

    def calculate(self, df, namespace, **kw):
        self._signals_buy = False
        self._signals_sell = False
        self.idx += 1
        self.current_date = get_datetime()
        self.log.info(str(self.idx) + ' - ' + str(self.current_date) + ' - ' + str(df.iloc[-1].price))
        self.log.info(str(df.iloc[0].name) + ' - ' + str(df.iloc[-1].name))
        self.log.info(f'Queuing {self.name} ML calculation')
        job = tasks.enqueue_ml_calculate(df, namespace, self.name, self.idx, self.current_date, self.hyper_params, df_final=self.df_final, **kw)
        self.current_job_id = job.id

    def record(self):
        q = Queue('ml', connection=tasks.CONN)
        job = q.fetch_job(self.current_job_id)

        self.log.info(f'Waiting for ML job: {self.current_job_id}')
        while not job.is_finished:
            pass
        self.log.info('Job complete, recording results')
        self.result, df_results_json, df_final_json, self._signals_buy, self._signals_sell, self.hyper_params = job.result
        self.current_job_id = None
        df_results = pd.read_json(df_results_json)
        self.df_results = self.df_results.append(df_results)
        self.df_final = pd.read_json(df_final_json)
        payload = {self.name: self.result}
        record(**payload)

    def analyze(self, namespace, data_freq, extra_results):
        job = tasks.enqueue_ml_analyze(namespace, self.name, self.df_final, self.df_results, data_freq, extra_results)


class XGBOOST(MLIndicator):

    def __init__(self, **kw):
        self.feature_selected_columns = []
        self.num_boost_rounds = None
        super(XGBOOST, self).__init__("XGBOOST", **kw)


class LIGHTGBM(MLIndicator):
    def __init__(self, **kw):
        self.feature_selected_columns = []
        self.num_boost_rounds = None
        super(LIGHTGBM, self).__init__("LIGHTGBM", **kw)
