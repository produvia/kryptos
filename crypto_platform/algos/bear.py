# Description of a bear market by investopedia
# http://www.investopedia.com/terms/b/bearmarket.asp?lgl=rira-baseline-vertical

from catalyst.api import order_target_percent, record, symbol, set_benchmark
from catalyst import run_algorithm
import pandas as pd

from logbook import Logger

CONFIG = None
NAMESPACE = 'bear_market'
log = Logger(NAMESPACE)

def initialize(context):
    context.ASSET_NAME = CONFIG.ASSET
    context.asset = symbol(context.ASSET_NAME)
    set_benchmark(context.asset)
    
    # Start this trading algorithm when market is bullish
    context.i = 0
    context.IS_MARKET_BEAR = False

def handle_data(context, data):

    # Get price history for the last two months. Find peak, bottom, and last
    # prices for the period
    price_history = data.history(context.asset, fields='price', bar_count=60, frequency="1d")
    peak = price_history.max()
    bottom = price_history.min()
    price = price_history.ix[-1]

    # Trading logic: 
    # If current price is more than 20% lower than highest-closing price over a
    # 2-month period, market enters Bear territory and algorithm sells all 
    # asset and holds only cash. Market exits bear market when prices are at 
    # least 20% higher than lowest-closing price over a 2-month period. In this
    # case, algorithm invests 90% of portfolio in the asset.
    if price < 0.75*peak :
        context.IS_MARKET_BEAR = True
    elif price > 1.2*bottom:
        context.IS_MARKET_BEAR = False
    
    if context.IS_MARKET_BEAR:
        order_target_percent(
            context.asset,
            0.3,
        )
    else:
        order_target_percent(
            context.asset,
            0.75,
        )
        
    Portfolio_cumulative_return = (context.portfolio.portfolio_value/context.portfolio.starting_cash-1)*100
    
    # Save values for later inspection
    record(price=price,
           peak=peak,
           bottom=bottom,
           cash=context.portfolio.cash,
           leverage=context.account.leverage,
           Portfolio_cumulative_return=Portfolio_cumulative_return,
    )

