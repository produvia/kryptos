import os
import numpy as np
import pandas as pd
from datetime import datetime

from tsfresh import extract_features, extract_relevant_features
from tsfresh.utilities.dataframe_functions import roll_time_series

def add_tsfresh_features(df, tsfresh_settings):

    # Prepare some columns useful for tsfresh
    n = df.shape[0]
    df['id'] = 1
    df['time'] = np.array(range(1, n + 1))
    excl = ['target', 'pred']
    cols = [c for c in df.columns if c not in excl]

    # Prepare rolling
    df_id_changed = roll_time_series(df[cols], column_id="id",
                            column_sort="time", column_kind=None,
                            rolling_direction=1,
                            max_timeshift=tsfresh_settings['window'])

    # Extract tsfresh features
    extracted_features = extract_features(df_id_changed,
                            default_fc_parameters=tsfresh_settings['kind'],
                            column_id="id", column_sort="time",
                            disable_progressbar=True, n_jobs=os.cpu_count())

    # merge originals and new features
    extracted_features['time'] = np.array(range(1, n + 1))
    df_tsfresh = pd.merge(df, extracted_features, on=['time'])

    return df_tsfresh


def add_dates_features(df, timestamp):
    df['year'] = timestamp.year
    df['month'] = timestamp.month
    df['weekofyear'] = timestamp.weekofyear
    df['week'] = timestamp.week
    df['weekday'] = timestamp.weekday()
    df['day'] = timestamp.day
    df['hour'] = timestamp.hour
    df['minute'] = timestamp.minute
    return df
