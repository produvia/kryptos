from catalyst.api import record
import matplotlib.pyplot as plt
import pandas as pd

from kryptos.utils import viz
from kryptos.strategy.indicators import AbstractIndicator
from kryptos.strategy.signals import utils
from kryptos.utils.ml.model import *
from kryptos.utils.ml.preprocessing import *
from kryptos.utils.ml.metric import *


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
        self.current_date = df.iloc[-1].name.date()

        # Prepare data to machine learning problem
        X_train, y_train, X_test = preprocessing_data(df)

        # Train XGBoost
        model = xgboost_train(X_train, y_train)

        # Predict results
        self.result = int(xgboost_test(model, X_test)[0])
        self.results_pred.append(self.result)
        self.results_real.append(int(df.iloc[-1].target))

        if self.signals_buy:
            self.log.debug("Signals BUY")
        elif self.signals_sell:
            self.log.debug("Signals SELL")

    def analyze(self, namespace):
        classification_metrics(namespace, self.results_real, self.results_pred)
