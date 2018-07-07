from datetime import datetime
import pandas as pd
pd.options.mode.chained_assignment = None # disable chained assignments

from kryptos.platform.settings import MLConfig as CONFIG


def preprocessing_data(df):
    """Preprocessing data to resolve a machine learning problem
    """
    timestamp = df.iloc[-1].name

    # Add feature engineering (date)
    if CONFIG.FE_DATES:
        df['year'] = timestamp.year
        df['month'] = timestamp.month
        df['weekofyear'] = timestamp.weekofyear
        df['week'] = timestamp.week
        df['weekday'] = timestamp.weekday()
        df['day'] = timestamp.day
        df['hour'] = timestamp.hour
        df['minute'] = timestamp.minute

    # Prepare signal classification problem (0=KEPP / 1=UP / 2=DOWN)
    df['last_price'] = df['price'].shift(1)
    df['target_past'] = 0 # 'KEEP'
    df.loc[df.last_price + (df.last_price * CONFIG.PERCENT_UP) < df.price, 'target_past'] = 1 # 'UP'
    df.loc[df.last_price - (df.last_price * CONFIG.PERCENT_DOWN) > df.price, 'target_past'] = 2 # 'DOWN'
    df['target'] = df['target_past'].shift(1).copy()
    df = df.dropna()
    df['target'] = df['target'].astype('int')

    # Prepare data struct
    excl = ['target', 'pred']
    X_train, y_train, X_test = prepare_data(df, excl, 'target')

    return X_train, y_train, X_test


def prepare_data(df, excl, target):
    cols = [c for c in df.columns if c not in excl]
    X_train = df[cols].iloc[:-1]
    y_train = df[target].iloc[:-1]
    X_test = df[cols].iloc[-1:]
    return X_train, y_train, X_test


# deprecated
def prepare_data2(df, row, excl, target):
    cols = [c for c in df.columns if c not in excl]
    X_train = df[cols]
    y_train = df[target]
    X_test = pd.DataFrame(columns=cols)
    X_test.loc[0] = row
    return X_train, y_train, X_test
