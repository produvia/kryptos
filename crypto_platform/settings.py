import os
import json


APP_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.dirname(APP_DIR)
PERF_DIR = os.path.join(BASE_DIR, "performance_results")
LOG_DIR = os.path.join(BASE_DIR, "logs")

STRAT_DIR = os.path.join(APP_DIR, "strategy")
DEFAULT_CONFIG_FILE = os.path.join(STRAT_DIR, "config.json")

with open(DEFAULT_CONFIG_FILE, "r") as f:
    DEFAULT_CONFIG = json.load(f)

# Optionally set metrics here instead of with the metrics "-m" option
METRICS = [
    # 'algo_volatility',
    # 'alpha',
    # 'benchmark_period_return',
    # 'benchmark_volatility',
    # 'beta',
    # 'gross_leverage',
    # 'long_exposure',
    # 'long_value',
    # 'longs_count',
    "max_drawdown",
    # 'max_leverage',
    # 'net_leverage',
    "pnl",
    "sharpe",
    # 'short_exposure',
    # 'short_value',
    # 'shorts_count',
    # 'sortino',
]


class TAConfig(object):

    BARS = 365

    # bbands_psar
    # MATYPE = ta.MA_Type.T3
    SAR_ACCEL = 0.02
    SAR_MAX = 0.2

    # macdfix
    MACD_SIGNAL = 9
    RSI_OVERSOLD = 55
    RSI_OVERBOUGHT = 65

    # mean_reversion
    RSI_OVERSOLD = 55
    RSI_OVERBOUGHT = 65
    CANDLE_SIZE = "5T"

    # rsi_profit_target
    MAX_HOLDINGS = 0.2
    RSI_OVERSOLD = 30
    RSI_OVERSOLD_BBANDS = 45
    RSI_OVERBOUGHT_BBANDS = 55

    # rsi_ta
    RSI_PERIOD = 7
    RSI_OVER_BOUGHT = 70
    RSI_OVER_SOLD = 30
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

    # stochastics
    STOCH_K_PERIOD = 5
    STOCH_D_PERIOD = 3
    STOCH_OVER_BOUGHT = 80
    STOCH_OVER_SOLD = 40

    RSI_OVERSOLD = 40
    RSI_OVERBOUGHT = 80

    STOCH_OVERBOUGHT = 80
    STOCH_OVERSOLD = 30
