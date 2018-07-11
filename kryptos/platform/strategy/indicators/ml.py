from catalyst.api import record
import matplotlib.pyplot as plt
import pandas as pd

from kryptos.platform.utils import viz
from kryptos.platform.strategy.indicators import AbstractIndicator
from kryptos.platform.strategy.signals import utils
from kryptos.platform.utils.ml.models.xgb import xgboost_train, xgboost_test, optimize_xgboost_params
from kryptos.platform.utils.ml.preprocessing import preprocessing_multiclass_data, clean_params, add_fe
from kryptos.platform.utils.ml.metric import classification_metrics
from kryptos.platform.settings import MLConfig as CONFIG
from kryptos.platform.utils import merge_two_dicts

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

    def calculate(self, df, **kw):
        """"""
        pass

    @property
    def signals_buy(self):
        """Used to define conditions for buy signal"""
        pass

    @property
    def signals_sell(self):
        """Used to define conditions for buy signal"""
        pass


class XGBOOST(MLIndicator):

    def __init__(self, **kw):
        super(XGBOOST, self).__init__("XGBOOST", **kw)
        self.num_boost_rounds = None

    @property
    def signals_buy(self):
        if self.result == 1:
            return True
        else:
            return False

    @property
    def signals_sell(self):
        if self.result == 2:
            return True
        else:
            return False

    def calculate(self, df, **kw):
        self.idx += 1

        if df.shape[0] > CONFIG.MIN_ROWS_TO_ML:
            if CONFIG.OPTIMIZE_PARAMS and (self.idx % CONFIG.ITERATIONS_OPTIMIZE) == 0:
                X_train_optimize, y_train_optimize, X_test_optimize = preprocessing_multiclass_data(df, to_optimize=True)
                y_test_optimize = df['target'].tail(CONFIG.SIZE_TEST_TO_OPTIMIZE).values
                # print('opmizing...')
                params = optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize)
                # print(params)
                self.num_boost_rounds = int(params['num_boost_rounds'])
                self.hyper_params = clean_params(params)

            # Prepare data to machine learning problem
            if CONFIG.CLASSIFICATION_TYPE == 3:
                X_train, y_train, X_test = preprocessing_multiclass_data(df)
            elif CONFIG.CLASSIFICATION_TYPE == 2:
                X_train, y_train, X_test = preprocessing_binary_data(df)

            # Train XGBoost
            model = xgboost_train(X_train, y_train, self.hyper_params, self.num_boost_rounds)

            # Predict results
            self.result = int(xgboost_test(model, X_test)[0])

            # Results
            self.results_pred.append(self.result)
            self.results_real.append(int(df.iloc[-1].target))

        else:
            self.result = 0

        if self.signals_buy:
            self.log.debug("Signals BUY")
        elif self.signals_sell:
            self.log.debug("Signals SELL")

    def analyze(self, namespace):
        file_name = 'xgboost_confussion_matrix.txt'
        classification_metrics(namespace, file_name, self.results_real, self.results_pred)
