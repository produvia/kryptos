import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.finance import candlestick_ohlc
import numpy as np
import pandas as pd
import talib as ta
from logbook import Logger


def chart(context, prices, analysis, results):
    results.portfolio_value.plot()

    # Data for matplotlib finance plot
    dates = date2num(prices.index.to_pydatetime())

    # Create the Open High Low Close Tuple
    prices_ohlc = [tuple([dates[i],
                          prices.open[i],
                          prices.high[i],
                          prices.low[i],
                          prices.close[i]]) for i in range(len(dates))]

    fig = plt.figure(figsize=(14, 18))

    # Draw the candle sticks
    ax1 = fig.add_subplot(411)
    ax1.set_ylabel(context.ASSET_NAME, size=20)
    candlestick_ohlc(ax1, prices_ohlc, width=0.4, colorup='g', colordown='r')

    # Draw Moving Averages
    analysis.sma_f.plot(ax=ax1, c='r')
    analysis.sma_s.plot(ax=ax1, c='g')

    # RSI
    ax2 = fig.add_subplot(412)
    ax2.set_ylabel('RSI', size=12)
    analysis.rsi.plot(ax=ax2, c='g',
                      label='Period: ' + str(context.RSI_PERIOD))
    analysis.sma_r.plot(ax=ax2, c='r',
                        label='MA: ' + str(context.RSI_AVG_PERIOD))
    ax2.axhline(y=30, c='b')
    ax2.axhline(y=50, c='black')
    ax2.axhline(y=70, c='b')
    ax2.set_ylim([0, 100])
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, labels)

    # Draw MACD computed with Talib
    ax3 = fig.add_subplot(413)
    ax3.set_ylabel('MACD: ' + str(context.MACD_FAST) + ', ' + str(
        context.MACD_SLOW) + ', ' + str(context.MACD_SIGNAL), size=12)
    analysis.macd.plot(ax=ax3, color='b', label='Macd')
    analysis.macdSignal.plot(ax=ax3, color='g', label='Signal')
    analysis.macdHist.plot(ax=ax3, color='r', label='Hist')
    ax3.axhline(0, lw=2, color='0')
    handles, labels = ax3.get_legend_handles_labels()
    ax3.legend(handles, labels)

    # Stochastic plot
    ax4 = fig.add_subplot(414)
    ax4.set_ylabel('Stoch (k,d)', size=12)
    analysis.stoch_k.plot(ax=ax4, label='stoch_k:' + str(context.STOCH_K),
                          color='r')
    analysis.stoch_d.plot(ax=ax4, label='stoch_d:' + str(context.STOCH_D),
                          color='g')
    handles, labels = ax4.get_legend_handles_labels()
    ax4.legend(handles, labels)
    ax4.axhline(y=20, c='b')
    ax4.axhline(y=50, c='black')
    ax4.axhline(y=80, c='b')

    plt.show()
    