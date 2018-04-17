from crypto_platform.strategy import Strategy
from crypto_platform.strategy.indicators import technical

import logbook

log = logbook.Logger('EXAMPLE')
log.level = logbook.INFO


strat = Strategy('Simple Stragey', data_frequency='daily')

bbands = technical.get_indicator('BBANDS')
bbands.update_param('matype', 'EMA')

stoch = technical.get_indicator('STOCH')

strat.add_market_indicator(bbands)
strat.add_market_indicator(stoch)

strat.use_dataset('quandl', columns=['MKTCP'])

strat.use_dataset('google', columns=['bitcoin futures'])
strat.add_data_indicator('google', 'relchange', col='bitcoin futures')

# trading config can be set via json or api
# Note that minute data is not supported for external datasets
# strat.trading_info['CAPITAL_BASE'] = 10000
# strat.trading_info['DATA_FREQ'] = 'minute'
# strat.trading_info['HISTORY_FREQ'] = '1m'
# strat.trading_info['START'] = '2017-12-10'
# strat.trading_info['END'] = '2017-12-11'


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
    log.info('Strategy Schema:\n{}'.format(strat.serialize()))
    strat.run()
