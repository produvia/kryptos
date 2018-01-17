# Description of a bear market by investopedia
# http://www.investopedia.com/terms/b/bearmarket.asp?lgl=rira-baseline-vertical

from catalyst.api import order_target_percent, record, symbol, set_benchmark
from catalyst import run_algorithm
import pandas as pd

from logbook import Logger

CONFIG = None
NAMESPACE = 'bear'
log = Logger(NAMESPACE)

def initialize(context):
    context.ASSET_NAME = CONFIG.ASSETS[0]
    # context.ASSET_NAME = 'btc_usdt'
    context.asset = symbol(context.ASSET_NAME)
    set_benchmark(context.asset)
    
    # For all trading pairs in the poloniex bundle, the default denomination
    # currently supported by Catalyst is 1/1000th of a full coin. Use this
    # constant to scale the price of up to that of a full coin if desired.
    context.TICK_SIZE = 1000.0
    
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

def analyze(context=None, results=None):
    import matplotlib.pyplot as plt
    import pandas as pd
    import sys
    import os
    from os.path import basename
    
    # Plot the portfolio and asset data.
    ax1 = plt.subplot(221)
    (context.TICK_SIZE * results[[
            'price',
            'peak',
            'bottom',
            ]]).plot(ax=ax1)
    ax1.set_ylabel('{asset} (USD)'.format(asset=context.ASSET_NAME))
    
    trans = results.ix[[t != [] for t in results.transactions]]
    buys = trans.ix[
        [t[0]['amount'] > 0 for t in trans.transactions]
    ]
    sells = trans.ix[
        [t[0]['amount'] < 0 for t in trans.transactions]
    ]

    ax1.plot(
        buys.index,
        context.TICK_SIZE * results.price[buys.index],
        '^',
        markersize=10,
        color='g',
    )
    ax1.plot(
        sells.index,
        context.TICK_SIZE * results.price[sells.index],
        'v',
        markersize=10,
        color='r',
    )

    ax2 = plt.subplot(222, sharex=ax1)
    ax2.set_ylabel('Percent Return (%)')
    results[[
            'algorithm_period_return',
            'benchmark_period_return',
    ]].plot(ax=ax2)


    ax3 = plt.subplot(223, sharex=ax1)
    results[['leverage']].plot(ax=ax3)
    ax3.set_ylabel('Leverage ')

    ax4 = plt.subplot(224, sharex=ax1)
    results[['cash']].plot(ax=ax4)
    ax4.set_ylabel('Cash (USD)')

    plt.legend(loc=3)

    # Show the plot.
    plt.gcf().set_size_inches(16, 8)
    plt.show()
    
    # Save results in CSV file
    filename = os.path.splitext(basename(sys.argv[3]))[0]
    results.to_csv(filename + '.csv')

if __name__ == '__main__':
    run_algorithm(
        capital_base=10000,
        data_frequency='daily',
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name='poloniex',
        base_currency='usdt',
        start=pd.to_datetime('2016-11-1', utc=True),
        end=pd.to_datetime('2017-11-10', utc=True),
    )
