import pandas as pd
from sklearn.preprocessing import StandardScaler, MaxAbsScaler, MinMaxScaler
pd.options.mode.chained_assignment = None # Disable chained assignments

from ml.settings import MLConfig as CONFIG
from ml.utils.feature_engineering import add_ta_features, add_ta_features2, add_dates_features, add_utils_features, add_tsfresh_features, add_fbprophet_features
from ml.utils import merge_two_dicts
from ml.models import xgb

def labeling_regression_data(df, data_freq, minute_freq, to_optimize=False):
    """Preprocessing data to resolve a regression machine learning problem.
    """
    # Prepare labelling classification problem (1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df = df.dropna()
    df['target_past'] = df['price'] - df['last_price']
    df['target'] = df['target_past'].shift(-1).copy()

    # Prepare data structure X and y
    excl = ['target', 'pred', 'id']
    cols = [c for c in df.columns if c not in excl]
    X = df[cols]
    y = df['target']

    X_train, y_train, X_test, y_test = _preprocessing_feature_engineering(X, y, data_freq, minute_freq, to_optimize)
    return X_train, y_train, X_test, y_test


def labeling_binary_data(df, data_freq, minute_freq, to_optimize=False):
    """Preprocessing data to resolve a multiclass (UP, DOWN) machine learning
    problem.
    """
    # Prepare labelling classification problem (1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df['target_past'] = 0 # 'KEEP & DOWN'
    df.loc[df.last_price < df.price, 'target_past'] = 1 # 'UP'
    df = df.dropna()
    df['diff_past'] = df['price'] - df['last_price']
    df['target'] = df['target_past'].astype('int').shift(-1).copy()

    # Prepare data structure X and y
    excl = ['target', 'pred', 'id']
    cols = [c for c in df.columns if c not in excl]
    X = df[cols]
    y = df['target']

    X_train, y_train, X_test, y_test = _preprocessing_feature_engineering(X, y, data_freq, minute_freq, to_optimize)
    return X_train, y_train.astype('int'), X_test, y_test


def clean_params(params, method):
    """
    """
    del params['num_boost_rounds']
    if 'max_depth' in params:
        params['max_depth'] = int(params['max_depth'])

    if method == 'XGBOOST':
        fixed_params_default = xgb.FIXED_PARAMS_DEFAULT

    elif method == 'LIGHTGBM':
        from ml.models import lgb
        params['num_leaves'] = int(params['num_leaves'])
        params['min_data_in_leaf'] = int(params['min_data_in_leaf'])
        params['bagging_freq'] = int(params['bagging_freq'])
        fixed_params_default = lgb.FIXED_PARAMS_DEFAULT

    else:
        raise NotImplementedError

    ml_params = merge_two_dicts(params, fixed_params_default)
    return ml_params


def labeling_multiclass_data(df, data_freq, minute_freq, to_optimize=False):
    """Preprocessing data to resolve a multiclass (UP, KEEP, DOWN) machine
    learning problem.
    """
    # Prepare labelling classification problem (0=KEPP / 1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df['target_past'] = 0 # 'KEEP'
    df.loc[df.last_price + (df.last_price * CONFIG.PERCENT_UP) < df.price, 'target_past'] = 1 # 'UP'
    df.loc[df.last_price - (df.last_price * CONFIG.PERCENT_DOWN) >= df.price, 'target_past'] = 2 # 'DOWN'
    df = df.dropna()
    df['diff_past'] = df['price'] - df['last_price']
    df['target'] = df['target_past'].astype('int').shift(-1).copy()

    # Prepare data structure X and y
    excl = ['target', 'pred', 'id']
    cols = [c for c in df.columns if c not in excl]
    X = df[cols]
    y = df['target']

    X_train, y_train, X_test, y_test = _preprocessing_feature_engineering(X, y, data_freq, minute_freq, to_optimize)
    return X_train, y_train.astype('int'), X_test, y_test


def normalize_data(X_train, y_train, X_test, name, method='diff'):
    """Normalize dataset. Please note that it doesn't modify the original
    dataset, it just returns a new dataset that you can use to modify
    the original dataset or create a new one.
    """
    if CONFIG.NORMALIZATION['method'] == 'max':
        scaler = MaxAbsScaler()
        scaler_y = MaxAbsScaler()
    elif CONFIG.NORMALIZATION['method'] == 'diff':
        scaler = MinMaxScaler()
        scaler_y = MinMaxScaler()
    elif CONFIG.NORMALIZATION['method'] == 'std':
        scaler = StandardScaler()
        scaler_y = StandardScaler()
    else:
        raise ValueError('Internal Error: Value of CONFIG.NORMALIZATION["method"] should be "max", "diff", "std".')

    aux = X_train
    X_train = scaler.fit_transform(X_train)
    X_train = pd.DataFrame(data=X_train, index=aux.index, columns=aux.columns)

    aux = X_test
    X_test = scaler.transform(X_test)
    X_test = pd.DataFrame(data=X_test, index=aux.index, columns=aux.columns)
    del aux

    y_train = scaler_y.fit_transform(y_train.values.reshape(-1, 1))

    if name == 'LIGHTGBM':
        y_train = [i[0] for i in y_train] # TODO: to do in a more efficient way

    return X_train, y_train, X_test, scaler_y


def inverse_normalize_data(result, scaler, method):
    if method == 'std':
        result = scaler.inverse_transform([float(result)])[0]
    elif method == 'max' or method == 'diff':
        result = scaler.inverse_transform(result)[0][0]
    else:
        raise ValueError('Internal Error: Value of CONFIG.NORMALIZATION["method"] should be "max", "diff", "std".')
    return result


def _preprocessing_feature_engineering(X, y, data_freq, minute_freq, to_optimize):
    if not to_optimize:

        # Adding different features (feature engineering)
        X = _add_fe(X, data_freq, minute_freq)

        # Drop nan values after feature engineering process
        X, y = _dropna_after_fe(X, y)

    # Prepare data struct
    X_train, y_train, X_test, y_test = _prepare_ml_data(X, y, to_optimize)

    return X_train, y_train, X_test, y_test


def _add_fe(df, data_freq, minute_freq):

    df['timestamp'] = df.index

    # Add tsfresh features
    if CONFIG.FE_TSFRESH['enabled']:
        df = add_tsfresh_features(df, CONFIG.FE_TSFRESH)

    # Add fbprophet features
    if CONFIG.FE_FBPROPHET['enabled']:
        df = add_fbprophet_features(df, data_freq, minute_freq, CONFIG.FE_FBPROPHET)

    # Add dates features
    if CONFIG.FE_DATES:
        df = add_dates_features(df)

    # Add ta-lib features
    if CONFIG.FE_TA['enabled']:
        df = add_ta_features(df, CONFIG.FE_TA)

    # Add ta bukosabino library features
    if CONFIG.FE_TA2:
        df = add_ta_features2(df, CONFIG.FE_TA2)

    # Add utils features
    if CONFIG.FE_UTILS:
        df = add_utils_features(df)

    excl = ['timestamp']
    cols = [c for c in df.columns if c not in excl]

    return df[cols]


def _dropna_after_fe(X, y):
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


def _prepare_ml_data(X, y, to_optimize=False):
    """Divide dataset on train and test dataset.

    Args:
        X(pandas.DataFrame): X dataset.
        y(pandas.DataFrame): target.
        optimize(bool): if False, size of test equals 1; if True equals
        CONFIG.OPTIMIZE_PARAMS['size'].

    Returns:
        X_train(pandas.DataFrame): X_train.
        y_train(pandas.DataFrame): y_train.
        X_test(pandas.DataFrame): X_test.
    """
    size_test = 1
    y_test = None
    if to_optimize:
        size_test = CONFIG.OPTIMIZE_PARAMS['size'] + 1
        y_test = y.iloc[-size_test:]
    X_train = X.iloc[:-size_test]
    y_train = y.iloc[:-size_test]
    X_test = X.iloc[-size_test:]
    return X_train, y_train, X_test, y_test
