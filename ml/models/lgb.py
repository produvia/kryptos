import lightgbm as lgb
import numpy as np
import multiprocessing

from ml.preprocessing import clean_params
from ml.utils import merge_two_dicts
from ml.settings import MLConfig as CONFIG


LIGHTGBM_SEED = 17


if CONFIG.CLASSIFICATION_TYPE == 1:
    FIXED_PARAMS_DEFAULT = {
        'boosting_type': 'gbdt',
        'objective': 'regression',
        'metric': {'l2', 'mse'}
    }

elif CONFIG.CLASSIFICATION_TYPE == 2:
    FIXED_PARAMS_DEFAULT = {
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'metric': 'binary_error'
    }

elif CONFIG.CLASSIFICATION_TYPE == 3:
    FIXED_PARAMS_DEFAULT = {
        'boosting_type': 'gbdt',
        'objective': 'softmax',
        'metric': 'softmax',
        'num_classes': 3
    }


else:
    raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')


FIXED_PARAMS = {
    'num_threads': multiprocessing.cpu_count(),
    'verbose': -1,
    'seed': LIGHTGBM_SEED
}


OPTIMIZABLE_PARAMS = {
    'num_leaves': 255,
    'learning_rate': 0.05,
    'bagging_fraction': 1, # 1
    'feature_fraction': 1, # 1
    'bagging_freq': 5,
    'max_depth': 20,
    'min_data_in_leaf': 350 # default=20
}


DEFAULT_PARAMS = merge_two_dicts(OPTIMIZABLE_PARAMS, FIXED_PARAMS)


def optimize_lightgbm_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize):
    raise NotImplementedError


def lightgbm_train(X_train, y_train, lgb_params=None, num_boost_rounds=None):
    if not lgb_params:
        lgb_params = merge_two_dicts(DEFAULT_PARAMS, FIXED_PARAMS_DEFAULT)

    if not num_boost_rounds:
        num_boost_rounds = 1200

    lgb_train = lgb.Dataset(X_train, y_train, silent=True)
    model = lgb.train(lgb_params, lgb_train, num_boost_round=num_boost_rounds)

    return model


def lightgbm_test(model, X_test):
    y_pred = model.predict(X_test, num_iteration = model.best_iteration)

    if CONFIG.CLASSIFICATION_TYPE == 1:
        y_pred = y_pred[0]

    elif CONFIG.CLASSIFICATION_TYPE == 2:
        if y_pred[0] > CONFIG.THRESHOLD and y_pred[0] <= 1.0:
            y_pred = 1
        elif y_pred[0] < CONFIG.THRESHOLD and y_pred[0] >= 0.0:
            y_pred = 0
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    elif CONFIG.CLASSIFICATION_TYPE == 3:
        y_pred = np.argmax(y_pred[0])

    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return y_pred
