ML_MODELS = ["XGBOOST", "LIGHTGBM"]

TRADE_TYPES = [("paper", "paper"), ("live", "live"), ("backtest", "backtest")]

FREQS = [("daily", "daily"), ("minute", "minute")]

DATASETS = [
    ("None", "None"),
    ("Google Trends, google"),
    ("Quandl Blochain Data", "quandl"),
]

EXISTING_STRATS = [
    ("BBANDS", "Bollinger Bands (BBANDS)"),
    ("SAR", "Stop and Reverse (SAR)"),
    ("MACD", "Moving Average Convergence/Divergence (MACD)"),
    ("MACDFIX", "Moving Average Convergence/Divergence Fix (MACDFIX)"),
    ("OBV", "On Balance Volume (OBV)"),
    ("RSI", "Relative Strength Index (RSI)"),
    ("STOCH", "Stochastic (STOCH)"),
    ("XGBOOST", "XGBOOST (ML)"),
    ("LIGHTGBM", "LIGHTGBM (ML)"),
]

EXCHANGES = [
    ("binance", "Binance"),
    ("bittrex", "Bittrex"),
    ("bitfinex", "Bitfinex"),
    ("poloniex", "Poloniex"),
]

SIGNAL_FUNCS = [
    ("decreasing", "Decreasing for"),
    ("increasing", "Increasing for"),
    ("cross_above", "Crosses Above"),
    ("cross_below", "Crosses Below"),
]

SIGNAL_TYPES = [("buy", "Buy"), ("sell", "Sell")]
