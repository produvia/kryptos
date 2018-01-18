import os
import pandas as pd

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
        'algo_volatility',
    #     'algorithm_period_return',
        # 'alpha',
    #     'benchmark_period_return',
    #     'benchmark_volatility',
        # 'beta',
    #     'capital_used',
        # 'cash',
    #     'ending_cash',
    #     'ending_exposure',
    #     'ending_value',
        # 'excess_return',
    #     'gross_leverage',
    #     'information',
        # 'leverage',
    #     'long_exposure',
    #     'long_value',
    #     'longs_count',
        'max_drawdown',
    #     'max_leverage',
    #     'net_leverage',
    #     'orders',
    #     'period_close',
    #     'period_label',
    #     'period_open',
        'pnl',
        'portfolio_value',
    #     'positions',
    #     'price',
    #     'returns',
        'sharpe',
    #     'short_exposure',
    #     'short_value',
    #     'shorts_count',
        'sortino',
    #     'starting_cash',
    #     'starting_exposure',
    #     'starting_value',
    #     'trading_days',
    #     'transactions',
    #     'treasury_period_return',
    #     'volume'
        ]