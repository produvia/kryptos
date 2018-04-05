from crypto_platform.strategy import Strategy
from crypto_platform.strategy.signals import utils

config = './sma_crossover.json'

strat = Strategy()

strat.load_from_json(config)


sma_fast = strat.indicator('SMA_FAST')
sma_slow = strat.indicator('SMA_SLOW')

@strat.signal_sell
def signal_sell(context, data):
    return utils.less_than(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)


@strat.signal_buy
def signal_buy(context, data):
    return utils.greater_than(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)


if __name__ == '__main__':
    print('Strategy:\n{}'.format(strat.serialize()))
    strat.run()
