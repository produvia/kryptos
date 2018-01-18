from os.path import basename
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.finance import candlestick_ohlc
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger

from catalyst.exchange.utils.stats_utils import extract_transactions, get_pretty_stats




def avg_order_prices(results):
    avg_buy, avg_sell = None, None
    # ax = plt.subplot(414)
    transaction_df = extract_transactions(results)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df['amount'] > 0]
        sell_df = transaction_df[transaction_df['amount'] < 0]

        avg_buy = buy_df.loc[:, 'price'].mean()
        avg_sell = sell_df.loc[:, 'price'].mean()

    text = "Average Buy Price:{}\nAverage Sell Price:{}".format(avg_buy, avg_sell)
    print(text)

    return avg_buy, avg_sell



    


