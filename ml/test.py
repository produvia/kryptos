"""File to test ml service"""
import pandas as pd
from worker import *

# read data
df = pd.read_csv('data/datas.csv', index_col="index", sep=',')
df_final = pd.DataFrame()

# prepare data
df = df.to_json()
name = 'LIGHTGBM'
idx = 0
current_datetime = pd.tslib.Timestamp('2016-03-03 00:00:00')
df_final_json = df_final.to_json()
data_freq = 'minute'
hyper_params = None

# calculate
results = calculate(df, name, idx, current_datetime, df_final_json, data_freq, hyper_params)
print('final')
