import pandas as pd
pd.options.mode.chained_assignment = None # Disable chained assignments

from kryptos.platform.settings import MLConfig as CONFIG
from kryptos.platform.utils.ml.feature_engineering import *


def preprocessing_data(df):
    """Preprocessing data to resolve a machine learning problem
    """
    timestamp = df.iloc[-1].name

    # Prepare signal classification problem (0=KEPP / 1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df['target_past'] = 0 # 'KEEP'
    df.loc[df.last_price + (df.last_price * CONFIG.PERCENT_UP) < df.price, 'target_past'] = 1 # 'UP'
    df.loc[df.last_price - (df.last_price * CONFIG.PERCENT_DOWN) > df.price, 'target_past'] = 2 # 'DOWN'
    df['target'] = df['target_past'].shift(1).copy()
    df = df.dropna()
    df['target'] = df['target'].astype('int')

    # Prepare tsfresh
    if CONFIG.FE_TSFRESH['enabled']:
        df = add_tsfresh_features(df, CONFIG.FE_TSFRESH)

    # Add feature engineering (date)
    if CONFIG.FE_DATES:
        df = add_dates_features(df, timestamp)

    # Prepare data struct
    excl = ['target', 'pred', 'id']
    X_train, y_train, X_test = prepare_ml_data(df, excl, 'target')

    return X_train, y_train, X_test


def prepare_ml_data(df, excl, target):
    cols = [c for c in df.columns if c not in excl]
    X_train = df[cols].iloc[:-1]
    y_train = df[target].iloc[:-1]
    X_test = df[cols].iloc[-1:]
    return X_train, y_train, X_test
