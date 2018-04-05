from crypto_platform.strategy import Strategy
from crypto_platform.strategy.signals import utils
from crypto_platform.utils import viz
import matplotlib.pyplot as plt

config = './sma_crossover.json'

strat = Strategy()

strat.load_from_json(config)


sma_fast = strat.indicator('SMA_FAST')
sma_slow = strat.indicator('SMA_SLOW')


@strat.signal_sell
def signal_sell(context, data):
    return utils.cross_below(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)


@strat.signal_buy
def signal_buy(context, data):
    return utils.cross_above(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)

@strat.analyze(num_plots=1)
def extra_plot(context, results, pos):
    viz.plot_column(results, 'SMA_FAST', pos, label='Fast', y_label='Crossover')
    viz.plot_column(results, 'SMA_SLOW', pos, label='Slow', y_label='Crossover')
    plt.legend()




if __name__ == '__main__':
    print('Strategy:\n{}'.format(strat.serialize()))
    strat.run()
