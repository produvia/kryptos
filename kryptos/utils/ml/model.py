import xgboost as xgb


def xgboost_train(X_train, y_train):
    xgb_params = {
        'n_trees': 800,
        'eta': 0.0045,
        'max_depth': 20,
        'subsample': 1,
        'colsample_bytree': 1,
        'colsample_bylevel': 1,
        'objective': 'multi:softmax',
        'num_class' : 3,
        'eval_metric': 'mlogloss', # 'merror', # 'rmse',
        'base_score': 0,
        'silent': 1
    }
    dtrain = xgb.DMatrix(X_train, y_train)
    num_boost_rounds = 705

    model = xgb.train(xgb_params, dtrain, num_boost_round=num_boost_rounds)
    return model


def xgboost_test(model, X_test):
    dtest = xgb.DMatrix(X_test)
    y_pred = model.predict(dtest)
    return y_pred
