import xgboost as xgb
from sklearn.metrics import cohen_kappa_score
import numpy as np

from kryptos.ml.preprocessing import clean_params
from kryptos.utils import merge_two_dicts
from kryptos.settings import MLConfig as CONFIG

XGBOOST_SEED = 17

if CONFIG.CLASSIFICATION_TYPE == 1:
    pass

elif CONFIG.CLASSIFICATION_TYPE == 2:
    FIXED_PARAMS_DEFAULT = {
        'objective': 'binary:logistic',
        'eval_metric': 'error@0.9', # 'error@0.9', auc
        'tree_method': 'exact', # TODO: gpu_exact
        'silent': 1,
        'seed': XGBOOST_SEED
    }

elif CONFIG.CLASSIFICATION_TYPE == 3:
    FIXED_PARAMS_DEFAULT = {
        'objective': 'multi:softmax',
        'num_class' : 3,
        'eval_metric': 'mlogloss', # 'merror', # 'rmse', # 'mlogloss'
        'base_score': 0,
        'tree_method': 'exact', # TODO: gpu_exact
        'silent': 1,
        'seed': XGBOOST_SEED
    }

else:
    raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

DEFAULT_PARAMS = {
    'n_trees': 800,
    'eta': 0.0045,
    'max_depth': 20,
    'subsample': 1,
    'colsample_bytree': 1,
    'colsample_bylevel': 1
}

def optimize_xgboost_params(X_train_optimize, y_train_optimize, X_test_optimize, y_test_optimize):
    # IMPLEMENTED ON https://github.com/produvia/kryptos/tree/ml-tsfresh
    # WAITING CATALYST UPDATE: https://github.com/enigmampc/catalyst/issues/269
    xgb_params = merge_two_dicts(DEFAULT_PARAMS, FIXED_PARAMS_DEFAULT)
    xgb_params['num_boost_rounds'] = 705
    return xgb_params


def xgboost_train(X_train, y_train, xgb_params=None, num_boost_rounds=None):

    if not xgb_params:
        xgb_params = merge_two_dicts(DEFAULT_PARAMS, FIXED_PARAMS_DEFAULT)

    if not num_boost_rounds:
        num_boost_rounds = 705

    dtrain = xgb.DMatrix(X_train, y_train)
    model = xgb.train(xgb_params, dtrain, num_boost_round=num_boost_rounds)
    return model


def xgboost_test(model, X_test):
    dtest = xgb.DMatrix(X_test)
    y_pred = model.predict(dtest)

    if CONFIG.CLASSIFICATION_TYPE == 1:
        pass

    elif CONFIG.CLASSIFICATION_TYPE == 2:
        if y_pred[0] > CONFIG.THRESHOLD and y_pred[0] <= 1.0:
            y_pred = 1
        elif y_pred[0] < CONFIG.THRESHOLD and y_pred[0] >= 0.0:
            y_pred = 0
        else:
            raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    elif CONFIG.CLASSIFICATION_TYPE == 3:
        y_pred = int(y_pred[0])

    else:
        raise ValueError('Internal Error: Value of CONFIG.CLASSIFICATION_TYPE should be 1, 2 or 3')

    return y_pred
