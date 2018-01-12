import os
import pandas as pd

class CONFIG(object):
    ASSETS = ['btc_usd']
    DATA_FREQUENCY = 'daily'
    HISTORY_FREQ = '1D'
    CAPITAL_BASE = 1000
    BUY_EXHANGE = 'bitfinex'
    SELL_EXCHANGE = 'bittrex'
    BASE_CURRENCY = 'usd'
    START = pd.to_datetime('2017-10-1', utc=True)
    END = pd.to_datetime('2017-10-2', utc=True)
    PERF_DIR = os.path.abspath('../performance_results')



ASSET_BY_SECTOR = {
    "digital_currency": [
        "ETH/BTC",
        "BCH/BTC",
        "MONA/BTC",
        "DOGE/BTC",
        "LTC/BTC",
        "OMG/BTC",
        "VTC/BTC",
        "BTG/BTC",
        "DGB/BTC"
    ],
    "identity": [
        "CVC/BTC",
        "FCT/BTC"
    ],
    "privacy": [
        "XMR/BTC",
        "XVG/BTC",
        "DASH/BTC",
        "KMD/BTC",
        "ZEC/BTC",
        "XZC/BTC",
        "PIVX/BTC",
        "BTCD/BTC",
        "NAV/BTC",
        "ENG/BTC",
        "ZCL/BTC"
    ],
    "smart_contract": [
        "NEO/BTC",
        "QTUM/BTC",
        "ADA/BTC",
        "LSK/BTC",
        "WAVES/BTC",
        "STRAT/BTC",
        "ETC/BTC",
        "NXT/BTC",
        "ARDR/BTC",
        "DCR/BTC"
    ],
    "gambling": [
        "FUN/BTC",
        "EDG/BTC"
    ],
    "gaming": [
        "MANA/BTC",
        "GAME/BTC",
        "VOX/BTC"
    ],
    "prediction": [
        "REP/BTC",
        "GNO/BTC"
    ],
    "lending": [
        "RCN/BTC",
        "SALT/BTC"
    ],
    "investment": [
    ],
    "payment": [
        "MTL/BTC",
        "XLM/BTC",
        "XRP/BTC"
    ],
    "credit": [
        "PAY/BTC",
        "MCO/BTC"
    ],
    "medical": [
        "PTOY/BTC"
    ],
    "ticketing": [
        "TIX/BTC"
    ],
    "social": [
        "SNT/BTC",
        "SYS/BTC",
        "RDD/BTC",
        "BAY/BTC"
    ],
    "ad_tech": [
        "BAT/BTC",
        "ADX/BTC"
    ],
    "energy": [
        "POWR/BTC"
    ],
    "insurance": [
    ],
    "exchanges": [
        "BNT/BTC"
    ],
    "storage_computing": [
        "SC/BTC",
        "STORJ/BTC",
        "GNT/BTC",
        "MAID/BTC"
    ],
    "cannabis": [
        "THC/BTC",
        "DOPE/BTC"
    ],
    "alt_blockchain": [
        "GBYTE/BTC"
    ],
    "connecting_tech": [
        "ARK/BTC",
        "XEM/BTC"
    ],
    "oracle": [
    ],
    "quantum_resistant": [
        "NXS/BTC",
        "QRL/BTC"
    ]
}
