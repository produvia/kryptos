import xgboost as xgb
from sklearn.metrics import *
from hyperopt import STATUS_OK, fmin, hp, tpe
from hyperopt.pyll.base import scope
import numpy as np

from kryptos.platform.utils.ml.preprocessing import clean_params
from kryptos.platform.utils import merge_two_dicts
from kryptos.platform.settings import MLConfig as CONFIG

FIXED_PARAMS_DEFAULT = {
    'objective': 'multi:softmax',
    'num_class' : 3,
    'eval_metric': 'mlogloss', # 'merror', # 'rmse', # 'mlogloss'
    'base_score': 0,
    'tree_method': 'exact', # TODO: gpu_exact
    'silent': 1,
    'seed': CONFIG.XGBOOST_SEED
}


def optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize):
    """
    This is the optimization function that given a space (space here) of
    hyperparameters and a scoring function (score here), finds the best hyperparameters.

    https://github.com/dmlc/xgboost/blob/master/doc/parameter.md
    """

    def score(params):

        num_boost_rounds = int(params['num_boost_rounds'])
        ml_params = clean_params(params)

        model = xgboost_train(X_train_optimize, y_train_optimize, ml_params, num_boost_rounds)
        y_pred = xgboost_test(model, X_test_optimize)

        score = cohen_kappa_score(y_test_optimize, y_pred) # TODO: test with other metrics.
        loss = 1 - score
        return {'loss': loss, 'status': STATUS_OK}

    space = {
        'num_boost_rounds': hp.quniform('num_boost_rounds', 400, 1200, 5),
        'n_trees': hp.quniform('n_trees', 400, 1200, 5),
        'eta': hp.quniform('eta', 0.001, 0.500, 0.010),
        'max_depth': scope.int(hp.quniform('max_depth', 14, 32, 1)),
        'min_child_weight': hp.quniform('min_child_weight', 1, 10, 1),
        'subsample': hp.quniform('subsample', 0.6, 1, 0.05),
        'colsample_bytree': hp.quniform('colsample_bytree', 0.6, 1, 0.05),
        'colsample_bylevel': hp.quniform('colsample_bylevel', 0.6, 1, 0.05)
        # 'gamma': hp.quniform('gamma', 0, 1, 0.2),
        # 'booster': hp.choice('booster', ['gbtree', 'dart']),
    }

    # Use the fmin function from Hyperopt to find the best hyperparameters
    best_hyperparameters = fmin(fn=score, space=space, algo=tpe.suggest,
                                    max_evals=CONFIG.N_HYPEROPT_EVALS)

    return best_hyperparameters


def xgboost_train(X_train, y_train, xgb_params=None, num_boost_rounds=None):

    if not xgb_params:
        params = {
            'n_trees': 800,
            'eta': 0.0045,
            'max_depth': 20,
            'subsample': 1,
            'colsample_bytree': 1,
            'colsample_bylevel': 1,
        }
        xgb_params = merge_two_dicts(params, FIXED_PARAMS_DEFAULT)

    if not num_boost_rounds:
        num_boost_rounds = 705

    dtrain = xgb.DMatrix(X_train, y_train)
    model = xgb.train(xgb_params, dtrain, num_boost_round=num_boost_rounds)
    return model


def xgboost_test(model, X_test):
    dtest = xgb.DMatrix(X_test)
    y_pred = model.predict(dtest)
    return y_pred
