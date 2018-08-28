from catalyst.api import get_datetime
import pandas as pd

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
        self.signals_buy = False
        self.signals_sell = False

    def calculate(self, df, name, **kw):
        self.signals_buy = False
        self.signals_sell = False
        self.idx += 1
        self.current_date = get_datetime()
        child_indicator = get_indicator(name)

        if CONFIG.DEBUG:
            self.log.info(str(self.idx) + ' - ' + str(self.current_date) + ' - ' + str(df.iloc[-1].price))
            self.log.info(str(df.iloc[0].name) + ' - ' + str(df.iloc[-1].name))

        job = tasks.enqueue_ml_calculate(df_current, name, self.idx, self.current_date, df_final=self.df_final, **kw)

        self.result, self.df_results, self.df_final, self.signals_buy, self.signals_sell = job.result


    def analyze(self, namespace, name, data_freq, extra_results):
        job = tasks.enqueue_ml_analyze(namespace, name, self.df_final, data_freq, extra_results)




class XGBOOST(MLIndicator):

    def __init__(self, **kw):
        self.feature_selected_columns = []
        self.num_boost_rounds = None
        super(XGBOOST, self).__init__("XGBOOST", **kw)


    @property
    def signals_buy(self):
        signal = False
        if CONFIG.CLASSIFICATION_TYPE == 1:
            if self.result > 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            if self.result == 1:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            if self.result == 1:
                signal = True
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
        return signal

    @property
    def signals_sell(self):
        signal = False
        if CONFIG.CLASSIFICATION_TYPE == 1:
            if self.result <= 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            if self.result == 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            if self.result == 2:
                signal = True
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
        return signal

    def calculate(self, df, **kw):
        super(XGBOOST, self).calculate(df, "XGBOOST", **kw)

    def analyze(self, namespace, extra_results):
        super(XGBOOST, self).analyze(namespace, "XGBOOST", extra_results)

    def train_test(self, X_train, y_train, X_test, hyper_params, num_boost_rounds):
        # Train
        model = xgboost_train(X_train, y_train, hyper_params, num_boost_rounds)
        # Predict
        result = xgboost_test(model, X_test)
        return result


class LIGHTGBM(MLIndicator):
    def __init__(self, **kw):
        self.feature_selected_columns = []
        self.num_boost_rounds = None
        super(LIGHTGBM, self).__init__("LIGHTGBM", **kw)

    @property
    def signals_buy(self):
        signal = False
        if CONFIG.CLASSIFICATION_TYPE == 1:
            if self.result > 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            if self.result == 1:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            if self.result == 1:
                signal = True
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
        return signal

    @property
    def signals_sell(self):
        signal = False
        if CONFIG.CLASSIFICATION_TYPE == 1:
            if self.result <= 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            if self.result == 0:
                signal = True
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            if self.result == 2:
                signal = True
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
        return signal

    def calculate(self, df, **kw):
        super(LIGHTGBM, self).calculate(df, "LIGHTGBM", **kw)

    def analyze(self, namespace, extra_results):
        super(LIGHTGBM, self).analyze(namespace, "LIGHTGBM", extra_results)

    def train_test(self, X_train, y_train, X_test, hyper_params, num_boost_rounds):
        # Train
        model = lightgbm_train(X_train, y_train, hyper_params, num_boost_rounds)
        # Predict
        result = lightgbm_test(model, X_test)
        return result
