from catalyst.api import record, get_datetime
import matplotlib.pyplot as plt
import pandas as pd

from kryptos.utils import viz
from kryptos.strategy.indicators import AbstractIndicator
from kryptos.strategy.signals import utils
from kryptos.ml.models.xgb import xgboost_train, xgboost_test, optimize_xgboost_params
from kryptos.ml.models.lgb import lightgbm_train, lightgbm_test
from kryptos.ml.feature_selection.xgb import xgb_embedded_feature_selection
from kryptos.ml.feature_selection.lgb import lgb_embedded_feature_selection
from kryptos.ml.feature_selection.filter import filter_feature_selection
from kryptos.ml.feature_selection.wrapper import wrapper_feature_selection
from kryptos.ml.preprocessing import labeling_multiclass_data, labeling_binary_data, labeling_regression_data, clean_params, normalize_data, inverse_normalize_data
from kryptos.ml.metric import classification_metrics
from kryptos.settings import MLConfig as CONFIG
from kryptos.settings import DEFAULT_CONFIG


def get_indicator(name, **kw):
    subclass = globals().get(name.upper())
    if subclass is not None:
        return subclass(**kw)

    return MLIndicator(name, **kw)

def _prepare_data(df):
    if CONFIG.CLASSIFICATION_TYPE == 1:
        X_train, y_train, X_test = labeling_regression_data(df)
    elif CONFIG.CLASSIFICATION_TYPE == 2:
        X_train, y_train, X_test = labeling_binary_data(df)
    elif CONFIG.CLASSIFICATION_TYPE == 3:
        X_train, y_train, X_test = labeling_multiclass_data(df)
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
    return X_train, y_train, X_test


def _optimize_hyper_params(df, idx):
    # Optimize Hyper Params for Xgboost model
    if CONFIG.OPTIMIZE_PARAMS['enabled'] and (idx % CONFIG.OPTIMIZE_PARAMS['iterations']) == 0:
        # Prepare data to machine learning problem
        if CONFIG.CLASSIFICATION_TYPE == 1:
            X_train_optimize, y_train_optimize, X_test_optimize = labeling_regression_data(df, to_optimize=True)
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            X_train_optimize, y_train_optimize, X_test_optimize = labeling_binary_data(df, to_optimize=True)
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            X_train_optimize, y_train_optimize, X_test_optimize = labeling_multiclass_data(df, to_optimize=True)
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

        y_test_optimize = df['target'].tail(CONFIG.OPTIMIZE_PARAMS['size']).values
        params = optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize)
        num_boost_rounds = int(params['num_boost_rounds'])
        hyper_params = clean_params(params)

        return num_boost_rounds, hyper_params
    return None, None

def _set_feature_selection(X_train, y_train, X_test, idx, hyper_params, num_boost_rounds):
    # Feature Selection
    if CONFIG.FEATURE_SELECTION['enabled'] and (idx % CONFIG.FEATURE_SELECTION['n_iterations']) == 0:
        method = CONFIG.FEATURE_SELECTION['method']
        if method == 'embedded':
            if name == 'XGBOOST':
                model = xgboost_train(X_train, y_train, hyper_params, num_boost_rounds)
                feature_selected_columns = xgb_embedded_feature_selection(model, 'all', 0.8)
            elif name == 'LIGHTGBM':
                feature_selected_columns = lgb_embedded_feature_selection(X_train, y_train)
            else:
                raise NotImplementedError
        elif method == 'filter':
            feature_selected_columns = filter_feature_selection(X_train, y_train, 0.8)
        elif method == 'wrapper':
            feature_selected_columns = wrapper_feature_selection(X_train, y_train, 0.4)
        else:
            raise ValueError('Internal Error: Value of CONFIG.FEATURE_SELECTION["method"] should be "embedded", "filter" or "wrapper"')

        return feature_selected_columns

def write_results_to_df():
    # Results
    df_results = pd.DataFrame(columns=['pred'])
    if CONFIG.CLASSIFICATION_TYPE == 1:
        df_results.loc[get_datetime()] = 1 if model_result > 0 else 0
    elif CONFIG.CLASSIFICATION_TYPE == 2 or CONFIG.CLASSIFICATION_TYPE == 3:
        df_results.loc[get_datetime()] = model_result
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return df_results

def calculate(df, name, idx, current_datetime, **kw):
    current_datetime = get_datetime()


    if CONFIG.DEBUG:
        self.log.info(str(self.idx) + ' - ' + str(current_datetime) + ' - ' + str(df.iloc[-1].price))
        self.log.info(str(df.iloc[0].name) + ' - ' + str(df.iloc[-1].name))

    # Dataframe size is enough to apply Machine Learning
    if df.shape[0] > CONFIG.MIN_ROWS_TO_ML:

        num_boost_rounds, hyper_params = _optimize_hyper_params(df, name, **kw)

        X_train, y_train, X_test = _prepare_data(df)

        feature_selected_columns = _set_feature_selection(X_train, y_train, X_test)

        if feature_selected_columns:
            X_train = X_train[feature_selected_columns]
            X_test = X_test[feature_selected_columns]

        if CONFIG.DEBUG:
            X_train_shape = X_train.shape
            self.log.info('X_train number of rows: {rows} number of columns {columns}'.format(
                                rows=X_train_shape[0], columns=X_train_shape[1]))

        # Normalize data
        if CONFIG.NORMALIZATION['enabled']:
            X_train, y_train, X_test, scaler_y = normalize_data(X_train, y_train, X_test, name, method=CONFIG.NORMALIZATION['method'])

        # Train and test indicator
        model_result = self.train_test(X_train, y_train, X_test, self.hyper_params, self.num_boost_rounds)

        # Revert normalization
        if CONFIG.NORMALIZATION['enabled']:
            model_result = inverse_normalize_data(model_result, scaler_y, CONFIG.NORMALIZATION['method'])

        df_results = write_df_results(model_result)

    else:
        model_result = 0

    # Fill df to analyze at end
    if idx == 0:
        self.df_final = df
        self.first_iteration = False
    else:
        self.df_final.loc[df.index[-1]] = df.iloc[-1]

    if CONFIG.DEBUG:
        # TODO: to log more details
        if self.signals_buy:
            self.log.info("buy signal")
        elif self.signals_sell:
            self.log.info("sell signal")
        else:
            self.log.info("keep signal")


    def analyze(self, namespace, name, extra_results):

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

        if name == 'XGBOOST':
            classification_metrics(namespace, 'xgboost_confussion_matrix.txt',
                                    self.results_real, self.results_pred, extra_results)
        elif name == 'LIGHTGBM':
            classification_metrics(namespace, 'lightgbm_confussion_matrix.txt',
                                    self.results_real, self.results_pred, extra_results)

    @property
    def signals_buy(self):
        pass

    @property
    def signals_sell(self):
        pass


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
