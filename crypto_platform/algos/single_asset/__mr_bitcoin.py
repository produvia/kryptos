"""Go long when the current price of the asset is more than 1 standard dev below its 30-day moving average and short in the opposite case
https://www.enigma.co/catalyst/#/strategy/5976e306ffa4a8000449cad9
"""

from catalyst.api import (
    order_target_percent,
    record,
    symbol,
    get_open_orders,
    set_max_leverage,
    schedule_function,
    date_rules,
    attach_pipeline,
    pipeline_output,
)

from catalyst.pipeline import Pipeline
from catalyst.pipeline.data import CryptoPricing
from catalyst.pipeline.factors.crypto import SimpleMovingAverage
from catalyst.pipeline.factors.crypto import AnnualizedVolatility
import math
from logbook import Logger
CONFIG = None
NAMESPACE = 'mr_bitcoin'
log = Logger(NAMESPACE)

def initialize(context):
    context.ASSET_NAME = CONFIG.ASSETS[0]
    context.WINDOW= 30

    # For all trading pairs in the poloniex bundle, the default denomination
    # currently supported by Catalyst is 1/1000th of a full coin. Use this
    # constant to scale the price of up to that of a full coin if desired.
    context.TICK_SIZE = 1000.0

    context.i = 0
    context.asset = symbol(context.ASSET_NAME)

    attach_pipeline(make_pipeline(context), 'mr_pipeline')

    schedule_function(
        handle_data,
        date_rules.every_day(),
    )

def before_trading_start(context, data):
    context.pipeline_data = pipeline_output('mr_pipeline')

def make_pipeline(context):
    return Pipeline(
        columns={
            'price': CryptoPricing.open.latest,
            'sma': SimpleMovingAverage(
                    inputs=[CryptoPricing.close],
                    window_length=context.WINDOW,
            ),
            'std': AnnualizedVolatility(
                    inputs=[CryptoPricing.close],
                    window_length=context.WINDOW,
                    annualization_factor=1,
            ),
        }
    )

# def rebalance(context, data):
def handle_data(context, data):
    context.i += 1

    # Skip first LONG_WINDOW bars to fill windows
    if context.i < context.WINDOW:
        return

    # Get pipeline data for asset of interest
    pipeline_data = context.pipeline_data
    pipeline_data = pipeline_data[pipeline_data.index == context.asset].iloc[0]

    # Compute the necessary statistics
    sma = pipeline_data.sma
    std = pipeline_data.std()
    price = pipeline_data.price
    
    # Compute buy and sell thresholds
    # Buy threshold is the simple moving average value plus one standard dev.
    # Sell threshold is the simple moving average value minus one standard dev.
    buy_threshold = sma-std/math.sqrt(context.WINDOW)
    sell_threshold = sma+std/math.sqrt(context.WINDOW)
    
    # Check that the order has not already been placed
    open_orders = get_open_orders()
    if context.asset not in open_orders:
        # check that the asset of interest can currently be traded
        if data.can_trade(context.asset):
            # Trading logic: if price is less than the buy threshold, mean 
            # reversion should drive price up. Algorithm invests 100% in the 
            # asset. In the opposite case, mean reversion should drive price 
            # down. Algorithm invests 50% in cash and 50% in the asset. If
            # price is between buy and sell thresholds, algorithm invests 25%
            # in cash and 75% in the asset.
            if price < buy_threshold:
                order_target_percent(
                    context.asset,
                    1.0,
                )
            elif price > sell_threshold:
                order_target_percent(
                    context.asset,
                    0.5,
                )
            else:
                order_target_percent(
                    context.asset,
                    0.75,
                )

    record(
        price=price,
        leverage=context.account.leverage,
        sma=sma,
        std=std,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold,
    )
    
def analyze(context=None, results=None):
    import matplotlib.pyplot as plt

    # Plot the portfolio and asset data.
    ax1 = plt.subplot(411)
    results[['portfolio_value']].plot(ax=ax1)
    ax1.set_ylabel('Portfolio value (USD)')

    ax2 = plt.subplot(412, sharex=ax1)
    ax2.set_ylabel('{asset} (USD)'.format(asset=context.ASSET_NAME))
    (context.TICK_SIZE*results[['price', 'sma', 'buy_threshold','sell_threshold']]).plot(ax=ax2)

    trans = results.ix[[t != [] for t in results.transactions]]
    amounts = [t[0]['amount'] for t in trans.transactions]

    buys = trans.ix[
        [t[0]['amount'] > 0 for t in trans.transactions]
    ]
    sells = trans.ix[
        [t[0]['amount'] < 0 for t in trans.transactions]
    ]

    ax2.plot(
        buys.index,
        context.TICK_SIZE * results.price[buys.index],
        '^',
        markersize=10,
        color='g',
    )
    ax2.plot(
        sells.index,
        context.TICK_SIZE * results.price[sells.index],
        'v',
        markersize=10,
        color='r',
    )

    ax3 = plt.subplot(413, sharex=ax1)
    results[['leverage']].plot(ax=ax3)
    ax3.set_ylabel('Leverage (USD)')

    results[[
        'algorithm',
        'benchmark',
    ]] = results[[
        'algorithm_period_return',
        'benchmark_period_return',
    ]]

    ax4 = plt.subplot(414, sharex=ax1)
    results[[
        'algorithm',
        'benchmark',
    ]].plot(ax=ax4)
    ax4.set_ylabel('Percent Change')

    plt.legend(loc=3)

    # Show the plot.
    plt.gcf().set_size_inches(18, 8)
    plt.show()