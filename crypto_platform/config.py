import os
import pandas as pd
import talib as ta

class CONFIG(object):
    ASSET = 'btc_usd'
    DATA_FREQUENCY = 'daily'
    HISTORY_FREQ = '1D'
    CAPITAL_BASE = 1000
    BUY_EXCHANGE = 'bitfinex'
    BASE_CURRENCY = 'usd'
    START = pd.to_datetime('2016-04-10', utc=True)
    END = pd.to_datetime('2018-01-2', utc=True)
    PERF_DIR = os.path.abspath('./performance_results')

    # For all trading pairs in the poloniex bundle, the default denomination
    # currently supported by Catalyst is 1/1000th of a full coin. Use this
    # constant to scale the price of up to that of a full coin if desired.
    TICK_SIZE = 1
    if BUY_EXCHANGE == 'poloniex':
        TICK_SIZE = 1000.0

    # Optionally set metrics here instead of with the metrics "-m" option
    METRICS = [
        # 'portfolio_value',
        # 'algorithm_period_return',
        # 'algo_volatility',
        # 'alpha',
        # 'benchmark_period_return',
        # 'benchmark_volatility',
        # 'beta',
        # 'capital_used',
        # 'cash',
        # 'ending_cash',
        # 'ending_exposure',
        # 'ending_value',
        # 'excess_return',
        # 'gross_leverage',
        # 'information',
        # 'long_exposure',
        # 'long_value',
        # 'longs_count',
        'max_drawdown',
        # 'max_leverage',
        # 'net_leverage',
        'pnl',
        # 'price',
        # 'returns',
        'sharpe',
        # 'short_exposure',
        # 'short_value',
        # 'shorts_count',
        # 'sortino',
        # 'starting_cash',
        # 'starting_exposure',
        # 'starting_value',
        # 'treasury_period_return',

        ]



class TAConfig(object):

    BARS = 365

    #bbands_psar
    MATYPE = ta.MA_Type.T3
    SAR_ACCEL = 0.02
    SAR_MAX = 0.2

     # macdfix
    MACD_SIGNAL = 9
    RSI_OVERSOLD = 55
    RSI_OVERBOUGHT = 65

    # mean_reversion
    RSI_OVERSOLD = 55
    RSI_OVERBOUGHT = 65
    CANDLE_SIZE = '5T'

    # rsi_profit_target
    MAX_HOLDINGS = 0.2
    RSI_OVERSOLD = 30
    RSI_OVERSOLD_BBANDS = 45
    RSI_OVERBOUGHT_BBANDS = 55

    # rsi_ta
    RSI_PERIOD = 14
    RSI_OVER_BOUGHT = 80
    RSI_OVER_SOLD = 20
    RSI_AVG_PERIOD = 15

    # sma_crossover
    SMA_FAST = 50
    SMA_SLOW = 100

    # sma_macd
    SMA_FAST = 50
    SMA_SLOW = 100
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9

    # stoch_rsi
    TIMEPERIOD = 9
    FASTK_PERIOD = 5
    FASTD_PERIOD = 3
    FASTD_MATYPE = 0
    STOCH_OVER_BOUGHT = 20
    STOCH_OVER_SOLD = 80

    #stochastics
    STOCH_K = 14
    STOCH_D = 3
    STOCH_OVER_BOUGHT = 80
    STOCH_OVER_SOLD = 20

        