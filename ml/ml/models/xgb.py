import xgboost as xgb
from sklearn.metrics import cohen_kappa_score, mean_squared_error
import numpy as np
from hyperopt import STATUS_OK, fmin, hp, tpe
from hyperopt.pyll.base import scope

from ml.utils.preprocessing import clean_params
from ml.utils import merge_two_dicts
from ml.settings import MLConfig as CONFIG


XGBOOST_SEED = 17


if CONFIG.CLASSIFICATION_TYPE == 1:
    FIXED_PARAMS_DEFAULT = {
        'objective': 'reg:linear',
        'tree_method': 'hist',
        'grow_policy': 'depthwise',
        'min_child_weight' : 160,
        'base_score': 0.0,
        'eval_metric': 'rmse'
    }
elif CONFIG.CLASSIFICATION_TYPE == 2:
    FIXED_PARAMS_DEFAULT = {
        'objective': 'binary:logistic',
        'eval_metric': 'error', # 'error@0.9', auc
        'tree_method': 'exact', # TODO: gpu_exact
        'seed': XGBOOST_SEED
    }
elif CONFIG.CLASSIFICATION_TYPE == 3:
    FIXED_PARAMS_DEFAULT = {
        'objective': 'multi:softmax',
        'num_class' : 3,
        'eval_metric': 'mlogloss', # 'merror', # 'rmse', # 'mlogloss'
        'base_score': 0.0,
        'tree_method': 'exact' # TODO: gpu_exact
    }
else:
    raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')


FIXED_PARAMS = {
    'silent': 1,
    'seed': XGBOOST_SEED
}


OPTIMIZABLE_PARAMS = {
    'n_trees': 800,
    'eta': 0.04, # 0.0045 0.05
    'max_depth': 30,
    'subsample': 1,
    'colsample_bytree': 1,
    'colsample_bylevel': 1
}


FIXED_PARAMS_DEFAULT = merge_two_dicts(FIXED_PARAMS_DEFAULT, FIXED_PARAMS)


def optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize):
    """
    This is the optimization function that given a space (space here) of
    hyperparameters and a scoring function (score here), finds the best hyperparameters.
    https://github.com/dmlc/xgboost/blob/master/doc/parameter.md
    """

    def score(params):
        num_boost_rounds = int(params['num_boost_rounds'])
        ml_params = clean_params(params, 'XGBOOST')
        model = xgboost_train(X_train_optimize, y_train_optimize, ml_params, num_boost_rounds)
        y_pred = xgboost_test(model, X_test_optimize)

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
        'num_boost_rounds': hp.quniform('num_boost_rounds', 400, 1200, 5),
        'n_trees': hp.quniform('n_trees', 400, 1200, 5),
        'eta': hp.quniform('eta', 0.001, 0.500, 0.010),
        'max_depth': scope.int(hp.quniform('max_depth', 14, 32, 1)),
        'min_child_weight': hp.quniform('min_child_weight', 1, 10, 1),
        'subsample': hp.quniform('subsample', 0.6, 1, 0.05),
        'colsample_bytree': hp.quniform('colsample_bytree', 0.6, 1, 0.05),
        'colsample_bylevel': hp.quniform('colsample_bylevel', 0.6, 1, 0.05)
    }

    # Use the fmin function from Hyperopt to find the best hyperparameters
    best_hyperparameters = fmin(fn=score, space=space, algo=tpe.suggest,
                                    max_evals=CONFIG.OPTIMIZE_PARAMS['n_evals'])

    return best_hyperparameters


def xgboost_train(X_train, y_train, xgb_params=None, num_boost_rounds=None):
    if not xgb_params:
        xgb_params = merge_two_dicts(OPTIMIZABLE_PARAMS, FIXED_PARAMS_DEFAULT)

    if not num_boost_rounds:
        num_boost_rounds = 705

    dtrain = xgb.DMatrix(X_train, y_train)
    model = xgb.train(xgb_params, dtrain, num_boost_round=num_boost_rounds)
    return model


def xgboost_test(model, X_test):
    dtest = xgb.DMatrix(X_test)
    y_pred = model.predict(dtest)

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
        y_pred = int(y_pred[0])
    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return y_pred
