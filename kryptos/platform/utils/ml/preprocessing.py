import pandas as pd
pd.options.mode.chained_assignment = None # Disable chained assignments

from kryptos.platform.settings import MLConfig as CONFIG
from kryptos.platform.utils.ml.feature_engineering import *
from kryptos.platform.utils import merge_two_dicts
from kryptos.platform.utils.ml.models import xgb

def preprocessing_binary_data(df):
    """Preprocessing data to resolve a multiclass (UP, KEEP, DOWN) machine
    learning problem.
    """
    # TODO:
    pass


def clean_params(params):
    """
    """
    del params['num_boost_rounds']
    params['max_depth'] = int(params['max_depth'])
    ml_params = merge_two_dicts(params, xgb.FIXED_PARAMS_DEFAULT)
    return ml_params


def preprocessing_multiclass_data(df, to_optimize=False):
    """Preprocessing data to resolve a multiclass (UP, KEEP, DOWN) machine
    learning problem.
    """

    # Prepare signal classification problem (0=KEPP / 1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df['target_past'] = 0 # 'KEEP'
    df.loc[df.last_price + (df.last_price * CONFIG.PERCENT_UP) < df.price, 'target_past'] = 1 # 'UP'
    df.loc[df.last_price - (df.last_price * CONFIG.PERCENT_DOWN) > df.price, 'target_past'] = 2 # 'DOWN'
    df['target'] = df['target_past'].shift(1).copy()
    df = df.dropna()
    df['target'] = df['target'].astype('int')

    excl = ['target', 'pred', 'id']
    cols = [c for c in df.columns if c not in excl]
    y = df['target']
    X = df[cols]

    if not to_optimize:
        # Adding different features (feature engineering)
        X = add_fe(X)

        # Drop nan values after feature engineering process
        X, y = dropna_after_fe(X, y)

    # Prepare data struct
    X_train, y_train, X_test = prepare_ml_data(X, y, to_optimize)

    return X_train, y_train, X_test


def add_fe(df):

    df['timestamp'] = df.index

    # Add tsfresh features
    if CONFIG.FE_TSFRESH['enabled']:
        df = add_tsfresh_features(df, CONFIG.FE_TSFRESH)

    # Add dates features
    if CONFIG.FE_DATES:
        df = add_dates_features(df)

    # Add ta-lib features
    if CONFIG.FE_TA['enabled']:
        df = add_ta_features(df, CONFIG.FE_TA)

    # Add fbprophet features
    if CONFIG.FE_FBPROPHET['enabled']:
        df = add_fbprophet_features(df, CONFIG.FE_FBPROPHET)

    # Add utils features
    if CONFIG.FE_UTILS:
        df = add_utils_features(df)

    excl = ['timestamp']
    cols = [c for c in df.columns if c not in excl]

    return df[cols]


def dropna_after_fe(X, y):
    """It drops Nan values on dataset from feature engineering process. Target
    column (y) needs the same size to X.

    Args:
        X(pandas.DataFrame): X dataset.
        y(pandas.DataFrame): target.
    Returns:
        X(pandas.DataFrame): X dataset without nan values.
        y(pandas.DataFrame): target same size to X.
    """
    X = X.dropna()
    y = y[len(y)-X.shape[0]:len(y)]
    return X, y


def prepare_ml_data(X, y, to_optimize=False):
    """Divide dataset on train and test dataset.

    Args:
        X(pandas.DataFrame): X dataset.
        y(pandas.DataFrame): target.
        optimize(bool): if False, size of test equals 1; if True equals
        CONFIG.SIZE_TEST_TO_OPTIMIZE.

    Returns:
        X_train(pandas.DataFrame): X_train.
        y_train(pandas.DataFrame): y_train.
        X_test(pandas.DataFrame): X_test.
    """
    size_test = 1
    if to_optimize:
        size_test = CONFIG.SIZE_TEST_TO_OPTIMIZE
    X_train = X.iloc[:-size_test]
    y_train = y.iloc[:-size_test]
    X_test = X.iloc[-size_test:]
    return X_train, y_train, X_test
