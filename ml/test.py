"""File to test ml service"""
import pandas as pd
from worker import *

# read data
df = pd.read_csv('data/datas.csv', index_col="index", sep=',')
df_final = pd.DataFrame()

# prepare data
df = df.to_json()
name = 'LIGHTGBM' # 'XGBOOST' # 'LIGHTGBM'
idx = 0
current_datetime = pd.tslib.Timestamp('2016-03-03 00:00:00')
df_final_json = df_final.to_json()
data_freq = 'minute'
minute_freq = "360"
hyper_params = None
namespace = 'inventado'

# calculate
results = calculate(namespace, df, 'LIGHTGBM', idx, current_datetime, df_final_json, data_freq, minute_freq, hyper_params)
results = calculate(namespace, df, 'XGBOOST', idx, current_datetime, df_final_json, data_freq, minute_freq, hyper_params)
print('final')
