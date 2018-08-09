from catalyst.api import record, get_datetime
import matplotlib.pyplot as plt
import pandas as pd

from kryptos.utils import viz
from kryptos.strategy.indicators import AbstractIndicator
from kryptos.strategy.signals import utils
from kryptos.ml.models.xgb import xgboost_train, xgboost_test, optimize_xgboost_params
from kryptos.ml.feature_selection.xgb import embedded_feature_selection
from kryptos.ml.feature_selection.filter import filter_feature_selection
from kryptos.ml.feature_selection.wrapper import wrapper_feature_selection
from kryptos.ml.preprocessing import labeling_multiclass_data, labeling_binary_data, labeling_regression_data, clean_params
from kryptos.ml.metric import classification_metrics
from kryptos.settings import MLConfig as CONFIG
from kryptos.settings import DEFAULT_CONFIG
from kryptos.utils import merge_two_dicts


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
        self.feature_selected_columns = []

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
        self.first_iteration = True
        self.current_date = None

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
        self.idx += 1
        self.current_date = get_datetime()

        if CONFIG.DEBUG:
            self.log.info(str(self.idx) + ' - ' + str(self.current_date) + ' - ' + str(df.iloc[-1].price))
            self.log.info(str(df.iloc[0].name) + ' - ' + str(df.iloc[-1].name))

        # Dataframe size is enough to apply Machine Learning
        if df.shape[0] > CONFIG.MIN_ROWS_TO_ML:

            # Optimize Hyper Params for Xgboost model
            if CONFIG.OPTIMIZE_PARAMS and (self.idx % CONFIG.ITERATIONS_PARAMS_OPTIMIZE) == 0:

                # Prepare data to machine learning problem
                if CONFIG.CLASSIFICATION_TYPE == 1:
                    X_train_optimize, y_train_optimize, X_test_optimize = labeling_regression_data(df, to_optimize=True)
                elif CONFIG.CLASSIFICATION_TYPE == 2:
                    X_train_optimize, y_train_optimize, X_test_optimize = labeling_binary_data(df, to_optimize=True)
                elif CONFIG.CLASSIFICATION_TYPE == 3:
                    X_train_optimize, y_train_optimize, X_test_optimize = labeling_multiclass_data(df, to_optimize=True)
                else:
                    raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

                y_test_optimize = df['target'].tail(CONFIG.SIZE_TEST_TO_OPTIMIZE).values
                params = optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize)
                self.num_boost_rounds = int(params['num_boost_rounds'])
                self.hyper_params = clean_params(params)

            # Prepare data to machine learning problem
            if CONFIG.CLASSIFICATION_TYPE == 1:
                X_train, y_train, X_test = labeling_regression_data(df)
            elif CONFIG.CLASSIFICATION_TYPE == 2:
                X_train, y_train, X_test = labeling_binary_data(df)
            elif CONFIG.CLASSIFICATION_TYPE == 3:
                X_train, y_train, X_test = labeling_multiclass_data(df)
            else:
                raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

            # Feature Selection
            if CONFIG.PERFORM_FEATURE_SELECTION and (self.idx % CONFIG.ITERATIONS_FEATURE_SELECTION) == 0:
                if CONFIG.TYPE_FEATURE_SELECTION == 'embedded':
                    model = xgboost_train(X_train, y_train, self.hyper_params, self.num_boost_rounds)
                    self.feature_selected_columns = embedded_feature_selection(model, 'all', 0.9)
                elif CONFIG.TYPE_FEATURE_SELECTION == 'filter':
                    self.feature_selected_columns = filter_feature_selection(X_train, y_train, 0.9)
                elif CONFIG.TYPE_FEATURE_SELECTION == 'wrapper':
                    self.feature_selected_columns = wrapper_feature_selection(X_train, y_train, 0.4)

            if self.feature_selected_columns:
                X_train = X_train[self.feature_selected_columns]
                X_test = X_test[self.feature_selected_columns]

            if CONFIG.DEBUG:
                X_train_shape = X_train.shape
                self.log.info('X_train number of rows: {rows} number of columns {columns}'.format(
                                    rows=X_train_shape[0], columns=X_train_shape[1]))

            # Train XGBoost
            model = xgboost_train(X_train, y_train, self.hyper_params, self.num_boost_rounds)

            # Predict results
            self.result = xgboost_test(model, X_test)

            # Results
            if CONFIG.CLASSIFICATION_TYPE == 1:
                self.df_results.loc[get_datetime()] = 1 if self.result > 0 else 0
            elif CONFIG.CLASSIFICATION_TYPE == 2 or CONFIG.CLASSIFICATION_TYPE == 3:
                self.df_results.loc[get_datetime()] = self.result
            else:
                raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

        else:
            self.result = 0

        # Fill df to analyze at end
        if self.first_iteration:
            self.df_final = df
            self.first_iteration = False
        else:
            self.df_final.loc[df.index[-1]] = df.iloc[-1]

        # TODO: to log more details
        if self.signals_buy:
            self.log.info("buy signal")
        elif self.signals_sell:
            self.log.info("sell signal")
        else:
            self.log.info("keep signal")

    def analyze(self, namespace):

        if CONFIG.CLASSIFICATION_TYPE == 1:
            # Post processing of target column
            self.df_final['target'] = 0 # 'KEEP - DOWN'
            self.df_final.loc[self.df_final.price < self.df_final.price.shift(-1), 'target'] = 1 # 'UP'
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            # Post processing of target column
            self.df_final['target'] = 0 # 'KEEP - DOWN'
            self.df_final.loc[self.df_final.price < self.df_final.price.shift(-1), 'target'] = 1 # 'UP'
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            # Post processing of target column
            self.df_final['target'] = 0 # 'KEEP'
            self.df_final.loc[self.df_final.price + (self.df_final.price * CONFIG.PERCENT_UP) < self.df_final.price.shift(-1), 'target'] = 1 # 'UP'
            self.df_final.loc[self.df_final.price - (self.df_final.price * CONFIG.PERCENT_DOWN) >= self.df_final.price.shift(-1), 'target'] = 2 # 'DOWN'
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

        if DEFAULT_CONFIG['DATA_FREQ'] == 'daily':
            self.results_pred = self.df_results.pred.astype('int').values
            self.results_real = self.df_final.loc[pd.to_datetime(self.df_results.index.date, utc=True)].target.values
        else:
            self.results_pred = self.df_results.pred.astype('int').values
            self.results_real = self.df_final.loc[self.df_results.index].target.values

        # Delete last item because of last results_real is not real.
        self.results_pred = self.results_pred[:-1]
        self.results_real = self.results_real[:-1]

        classification_metrics(namespace, 'xgboost_confussion_matrix.txt',
                                self.results_real, self.results_pred)
