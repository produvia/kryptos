from kryptos.strategy import Strategy
from kryptos.strategy.indicators import technical
# from kryptos.strategy.signals import utils
# from kryptos.utils import viz
# import matplotlib.pyplot as plt
import logbook

log = logbook.Logger('EXAMPLE')
log.level = logbook.INFO

strat = Strategy('MacdFix')

macdfix_9 = technical.get_indicator('MACDFIX', label='MACDFIX_9')

macdfix_18 = technical.get_indicator('MACDFIX', label='MACDFIX_18')
macdfix_18.update_param('signalperiod', 18)


strat.add_market_indicator(macdfix_9)
strat.add_market_indicator(macdfix_18)

@strat.init
def init(context):
    log.info('Algo is being initialzed, setting up context')
    context.i = 0


@strat.handle_data
def handle_data(context, data):
    log.debug('Processing new trading step')
    context.i += 1


@strat.analyze()
def analyze(context, results, pos):
    ending_cash = results.cash[-1]
    log.info('Ending cash: ${}'.format(ending_cash))
    log.info('Completed for {} trading periods'.format(context.i))

if __name__ == '__main__':
    strat.run()
