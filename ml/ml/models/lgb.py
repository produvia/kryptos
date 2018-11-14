import lightgbm as lgb
from sklearn.metrics import cohen_kappa_score, mean_squared_error
import numpy as np
import multiprocessing
from hyperopt import STATUS_OK, fmin, hp, tpe
from hyperopt.pyll.base import scope

from ml.utils.preprocessing import clean_params
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
    'max_depth': -1,
    'verbose': -1,
    'seed': LIGHTGBM_SEED
}


OPTIMIZABLE_PARAMS = {
    'num_leaves': 255,
    'learning_rate': 0.05,
    'bagging_fraction': 1, # 1
    'feature_fraction': 1, # 1
    'bagging_freq': 5,
    # 'max_depth': -1,
    'min_data_in_leaf': 350 # default=20
}

FIXED_PARAMS_DEFAULT = merge_two_dicts(FIXED_PARAMS_DEFAULT, FIXED_PARAMS)


def optimize_lightgbm_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize):
    """
    This is the optimization function that given a space (space here) of
    hyperparameters and a scoring function (score here), finds the best hyperparameters.
    https://github.com/Microsoft/LightGBM/blob/master/docs/Parameters.rst
    """

    def score(params):
        num_boost_rounds = int(params['num_boost_rounds'])
        ml_params = clean_params(params, 'LIGHTGBM')
        model = lightgbm_train(X_train_optimize, y_train_optimize, ml_params, num_boost_rounds)
        y_pred = lightgbm_test(model, X_test_optimize)

        if CONFIG.CLASSIFICATION_TYPE == 1:
            score = mean_squared_error(y_test_optimize, y_pred)
        elif CONFIG.CLASSIFICATION_TYPE == 2:
            score = cohen_kappa_score(y_test_optimize, y_pred) # TODO: test with other metrics.
        elif CONFIG.CLASSIFICATION_TYPE == 3:
            score = cohen_kappa_score(y_test_optimize, y_pred) # TODO: test with other metrics.
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

        loss = 1 - score
        return {'loss': loss, 'status': STATUS_OK}

    space = {
        'num_boost_rounds': hp.quniform('num_boost_rounds', 400, 1200, 50),
        'num_leaves': hp.quniform('num_leaves', 63, 511, 64),
        # 'learning_rate': hp.quniform('learning_rate', 0.001, 0.500, 0.010),
        'learning_rate': hp.uniform('learning_rate', 0.005, 0.500),
        'bagging_fraction': hp.quniform('bagging_fraction', 0.6, 1, 0.05),
        'feature_fraction': hp.quniform('feature_fraction', 0.6, 1, 0.05),
        'bagging_freq': hp.quniform('bagging_freq', 0, 20, 2),
        # 'max_depth': hp.quniform('max_depth', -1, 30, 5),
        'min_data_in_leaf': hp.quniform('min_data_in_leaf', 0, 500, 50)
    }

    # Use the fmin function from Hyperopt to find the best hyperparameters
    best_hyperparameters = fmin(fn=score, space=space, algo=tpe.suggest,
                                    max_evals=CONFIG.OPTIMIZE_PARAMS['n_evals'])

    return best_hyperparameters


def lightgbm_train(X_train, y_train, lgb_params=None, num_boost_rounds=None):
    if not lgb_params:
        lgb_params = merge_two_dicts(OPTIMIZABLE_PARAMS, FIXED_PARAMS_DEFAULT)

    if not num_boost_rounds:
        num_boost_rounds = 1200

    lgb_train = lgb.Dataset(X_train, y_train, silent=True)
    model = lgb.train(lgb_params, lgb_train, num_boost_round=num_boost_rounds)

    return model


def lightgbm_test(model, X_test):
    y_pred = model.predict(X_test, num_iteration = model.best_iteration)

    if CONFIG.CLASSIFICATION_TYPE == 1:
        if len(y_pred) == 1:
            y_pred = y_pred[0]
    elif CONFIG.CLASSIFICATION_TYPE == 2: # TODO: check with optimization
        if y_pred[0] > CONFIG.THRESHOLD and y_pred[0] <= 1.0:
            y_pred = 1
        elif y_pred[0] < CONFIG.THRESHOLD and y_pred[0] >= 0.0:
            y_pred = 0
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')
    elif CONFIG.CLASSIFICATION_TYPE == 3: # TODO: check with optimization
        y_pred = np.argmax(y_pred[0])
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return y_pred
