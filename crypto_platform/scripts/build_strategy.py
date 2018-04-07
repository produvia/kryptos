import click
import logbook
import uuid

from crypto_platform.strategy import Strategy
from crypto_platform.data.manager import AVAILABLE_DATASETS
from crypto_platform import logger_group


log = logbook.Logger('Platform')
logger_group.add_logger(log)


@click.command()
@click.option('--market-indicators', '-ta', multiple=True, help='Market Indicators listed in order of priority')
@click.option('--dataset', '-d', type=click.Choice(AVAILABLE_DATASETS), help='Include asset in keyword list')
@click.option('--columns', '-c', multiple=True, help='Target columns for specified dataset')
@click.option('--data-indicators', '-i', multiple=True, help='Dataset indicators')
@click.option('--json-file', '-f')
@click.option('--paper', is_flag=True, help='Run the strategy in Paper trading mode')
def run(market_indicators, dataset, columns, data_indicators, json_file, paper):

    strat = Strategy()

    columns = list(columns)

    for i in market_indicators:
        strat.add_market_indicator(i.upper())

    # currently assigns -i indicator to the column provided at the same index
    if dataset is not None:
        strat.use_dataset(dataset, columns)
        for i, ind in enumerate(data_indicators):
            strat.add_data_indicator(dataset, ind.upper(), col=columns[i])

    if json_file is not None:
        strat.load_from_json(json_file)

    @strat.init
    def initialize(context):
        log.info('Initializing strategy')
        pass

    @strat.handle_data
    def handle_data(context, data):
        log.debug('Doing extra stuff for handling data')
        pass

    @strat.analyze()
    def analyze(context, results, pos):
        log.info('Analyzing strategy')
        pass

    click.secho(strat.serialize(), fg='white')

    strat.run(live=paper)
