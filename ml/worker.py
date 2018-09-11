import os
import multiprocessing
import time
import sys
import logging
import redis
from rq import Connection, Queue
from rq.worker import HerokuWorker as Worker
import logbook
from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry
import pandas as pd
import logbook

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from ml.models.xgb import xgboost_train, xgboost_test, optimize_xgboost_params
from ml.models.lgb import lightgbm_train, lightgbm_test, optimize_lightgbm_params
from ml.feature_selection.xgb import xgb_embedded_feature_selection
from ml.feature_selection.lgb import lgb_embedded_feature_selection
from ml.feature_selection.filter import filter_feature_selection
from ml.feature_selection.wrapper import wrapper_feature_selection
from ml.utils.preprocessing import labeling_multiclass_data, labeling_binary_data, labeling_regression_data, clean_params, normalize_data, inverse_normalize_data
from ml.utils.metric import classification_metrics
from ml.utils.feature_exploration import visualize_model
from ml.settings import MLConfig as CONFIG, get_from_datastore

from google.cloud import datastore

log = logbook.Logger('ML_INDICATOR')
handler = logbook.StreamHandler(sys.stdout, level="INFO", bubble=True)
handler.push_application()

SENTRY_DSN =  os.getenv('SENTRY_DSN', None)
client = Client(SENTRY_DSN, transport=HTTPTransport)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-19779.c1.us-central1-2.gce.cloud.redislabs.com')
REDIS_PORT = os.getenv('REDIS_PORT', 19779)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) or get_from_datastore('REDIS_PASSWORD', 'production')
CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

def _prepare_data(df, data_freq):
    if CONFIG.CLASSIFICATION_TYPE == 1:
        X_train, y_train, X_test, y_test = labeling_regression_data(df, data_freq)
    elif CONFIG.CLASSIFICATION_TYPE == 2:
        X_train, y_train, X_test, y_test = labeling_binary_data(df, data_freq)
    elif CONFIG.CLASSIFICATION_TYPE == 3:
        X_train, y_train, X_test, y_test = labeling_multiclass_data(df, data_freq)
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
    return X_train, y_train, X_test


def _optimize_hyper_params(df, name, data_freq, idx, hyper_params):
    num_boost_rounds = None
    # Optimize Hyper Params for Xgboost model
    if CONFIG.OPTIMIZE_PARAMS['enabled'] and idx % CONFIG.OPTIMIZE_PARAMS['iterations'] == 0:
        # Prepare data to machine learning problem
        if CONFIG.CLASSIFICATION_TYPE == 1:
            X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize = labeling_regression_data(df, data_freq, to_optimize=True)
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize = labeling_binary_data(df, data_freq, to_optimize=True)
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize = labeling_multiclass_data(df, data_freq, to_optimize=True)
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

        if name == 'XGBOOST':
            params = optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize[0:-1], y_test_optimize[0:-1])
        elif name == 'LIGHTGBM':
            params = optimize_lightgbm_params(X_train_optimize, y_train_optimize, X_test_optimize[0:-1], y_test_optimize[0:-1])
        else:
            raise NotImplementedError

        num_boost_rounds = int(params['num_boost_rounds'])
        hyper_params = clean_params(params, name)

    return num_boost_rounds, hyper_params


def _set_feature_selection(name, X_train, y_train, X_test, idx, hyper_params, num_boost_rounds):
    # Feature Selection
    feature_selected_columns = []
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


def lgb_train_test(X_train, y_train, X_test, hyper_params, num_boost_rounds):
    # Train
    model = lightgbm_train(X_train, y_train, hyper_params, num_boost_rounds)
    # Predict
    result = lightgbm_test(model, X_test)
    return model, result


def xgb_train_test(X_train, y_train, X_test, hyper_params, num_boost_rounds):
    # Train
    model = xgboost_train(X_train, y_train, hyper_params, num_boost_rounds)
    # Predict
    result = xgboost_test(model, X_test)
    return model, result


def get_model_result(name, X_train, y_train, X_test, hyper_params, num_boost_rounds):
    # Train and test indicator
    if name == 'XGBOOST':
        model, result = xgb_train_test(X_train, y_train, X_test, hyper_params, num_boost_rounds)
    elif name == 'LIGHTGBM':
        model, result = lgb_train_test(X_train, y_train, X_test, hyper_params, num_boost_rounds)
    return model, result


def write_results_to_df(model_result, current_datetime):
    # Results
    df_results = pd.DataFrame(columns=['pred'])
    if CONFIG.CLASSIFICATION_TYPE == 1:
        df_results.loc[current_datetime] = 1 if model_result > 0 else 0
    elif CONFIG.CLASSIFICATION_TYPE == 2 or CONFIG.CLASSIFICATION_TYPE == 3:
        df_results.loc[current_datetime] = model_result
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return df_results


def signals_buy(model_result):
    signal = False
    if CONFIG.CLASSIFICATION_TYPE == 1:
        if model_result > 0:
            signal = True
    elif CONFIG.CLASSIFICATION_TYPE == 2:
        if model_result == 1:
            signal = True
    elif CONFIG.CLASSIFICATION_TYPE == 3:
        if model_result == 1:
            signal = True
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
    return signal


def signals_sell(model_result):
    signal = False
    if CONFIG.CLASSIFICATION_TYPE == 1:
        if model_result <= 0:
            signal = True
    elif CONFIG.CLASSIFICATION_TYPE == 2:
        if model_result == 0:
            signal = True
    elif CONFIG.CLASSIFICATION_TYPE == 3:
        if model_result == 2:
            signal = True
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
    return signal


def calculate(namespace, df_current_json, name, idx, current_datetime, df_final_json, data_freq, hyper_params, **kw):
    df_current = pd.read_json(df_current_json)
    df_final = pd.read_json(df_final_json)

    if CONFIG.DEBUG:
        log.info(hyper_params)
        log.info(str(idx) + ' - ' + str(current_datetime) + ' - ' + str(df_current.iloc[-1].price))
        log.info('from ' + str(df_current.iloc[0].name) + ' - to ' + str(df_current.iloc[-1].name))

    # Dataframe size is enough to apply Machine Learning
    if df_current.shape[0] > CONFIG.MIN_ROWS_TO_ML:

        num_boost_rounds, hyper_params = _optimize_hyper_params(df_current, name, data_freq, idx, hyper_params, **kw)

        X_train, y_train, X_test = _prepare_data(df_current, data_freq)

        feature_selected_columns = _set_feature_selection(name, X_train, y_train, X_test, idx, hyper_params, num_boost_rounds)

        if feature_selected_columns:
            X_train = X_train[feature_selected_columns]
            X_test = X_test[feature_selected_columns]

        if CONFIG.DEBUG:
            X_train_shape = X_train.shape
            log.info('X_train number of rows: {rows} number of columns {columns}'.format(
                                rows=X_train_shape[0], columns=X_train_shape[1]))

        # Normalize data
        if CONFIG.NORMALIZATION['enabled']:
            X_train, y_train, X_test, scaler_y = normalize_data(X_train, y_train, X_test, name, method=CONFIG.NORMALIZATION['method'])

        # Train and test indicator
        model, result = get_model_result(name, X_train, y_train, X_test, hyper_params, num_boost_rounds)

        # Revert normalization
        if CONFIG.NORMALIZATION['enabled']:
            result = inverse_normalize_data(result, scaler_y, CONFIG.NORMALIZATION['method'])

        df_results = write_results_to_df(result, current_datetime)

        visualize_model(model, X_train, idx, CONFIG.VISUALIZE_MODEL, namespace, name)

    else:
        model_result = 0

    buy = signals_buy(result)
    sell = signals_sell(result)

    # Fill df to analyze at end
    if idx == 0:
        df_final = df_current
    else:
        df_final.loc[df_current.index[-1]] = df_current.iloc[-1]

    log.info(f'Result: {result}')
    logging.info(result, df_results.to_json(), df_final.to_json(), buy, sell)
    return result, df_results.to_json(), df_final.to_json(), buy, sell, hyper_params


def analyze(namespace, name, df_final_json, df_results_json, data_freq, extra_results):
    df_final = pd.read_json(df_final_json)
    df_results = pd.read_json(df_results_json)

    if CONFIG.CLASSIFICATION_TYPE == 1:
        # Post processing of target column
        df_final['target'] = 0 # 'KEEP - DOWN'
        df_final.loc[df_final.price < df_final.price.shift(-1), 'target'] = 1 # 'UP'
    elif CONFIG.CLASSIFICATION_TYPE == 2:
        # Post processing of target column
        df_final['target'] = 0 # 'KEEP - DOWN'
        df_final.loc[df_final.price < df_final.price.shift(-1), 'target'] = 1 # 'UP'
    elif CONFIG.CLASSIFICATION_TYPE == 3:
        # Post processing of target column
        df_final['target'] = 0 # 'KEEP'
        df_final.loc[df_final.price + (df_final.price * CONFIG.PERCENT_UP) < df_final.price.shift(-1), 'target'] = 1 # 'UP'
        df_final.loc[df_final.price - (df_final.price * CONFIG.PERCENT_DOWN) >= df_final.price.shift(-1), 'target'] = 2 # 'DOWN'
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    if data_freq == 'daily':
        results_pred = df_results.pred.astype('int').values
        results_real = df_final.loc[pd.to_datetime(df_results.index.date, utc=True)].target.values
    else:
        results_pred = df_results.pred.astype('int').values
        results_real = df_final.loc[df_results.index].target.values

    # Delete last item because of last results_real is not real.
    results_pred = results_pred[:-1]
    results_real = results_real[:-1]

    if name == 'XGBOOST':
        classification_metrics(namespace, 'xgboost_confussion_matrix.txt',
                                results_real, results_pred, extra_results)
    elif name == 'LIGHTGBM':
        classification_metrics(namespace, 'lightgbm_confussion_matrix.txt',
                                results_real, results_pred, extra_results)


def manage_workers():
    # import before starting worker to loading during worker process
    # from kryptos.strategy import Strategy
    # from app.extensions import jsonrpc
    # from kryptos.utils.outputs import in_docker

    #start main worker
    with Connection(CONN):
        log.info('Starting initial ML worker')

        backtest_worker = Worker(['ml'])
        register_sentry(client, backtest_worker)
        multiprocessing.Process(target=backtest_worker.work, kwargs={'logging_level': 'ERROR'}).start()

        while True:
            q = Queue('ml', connection=CONN)
            required = len(q)
            # log.info(f"{required} workers required for {q.name}")
            for i in range(required):
                log.info(f"Creating {q.name} worker")
                worker = Worker([q.name])
                register_sentry(client, worker)
                multiprocessing.Process(target=worker.work, kwargs={'burst': True, 'logging_level': 'ERROR'}).start()

            time.sleep(5)


if __name__ == '__main__':
    manage_workers()
