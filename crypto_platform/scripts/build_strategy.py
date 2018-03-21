import click
from logbook import Logger

from crypto_platform.strategy import Strategy
from crypto_platform.data.manager import AVAILABLE_DATASETS


log = Logger('Blockchain Activity')



@click.command()
@click.option('--market-indicators', '-t', multiple=True, help='Market Indicators listed in order of priority')
@click.option('--dataset', '-d', type=click.Choice(AVAILABLE_DATASETS), help='Include asset in keyword list')
@click.option('--columns', '-c', multiple=True, help='Target columns for specified dataset')
@click.option('--data-indicators', '-i', multiple=True, help='Dataset indicators')


def run(market_indicators, dataset, columns, data_indicators):
    click.secho('''
        Creating Trading Strategy:
        Market Indicators: {}
        Dataset: {}
        Dataset Columns: {}
        Dataset Indicators: {}
        '''.format(market_indicators, dataset, columns, data_indicators), fg='white')

    strat = Strategy()

    columns = list(columns)

    for i in market_indicators:
        strat.add_market_indicator(i.upper())

    if dataset is not None:
        strat.use_dataset(dataset, columns)
        for i in data_indicators:
            strat.add_data_indicator(dataset, i.upper())

    @strat.init
    def initialize(context):
        log.info('Initializing strategy')

    @strat.handle_data
    def handle_data(context, data):
        log.info('Doing extra stuff for handling data')

    @strat.analyze
    def analyze(context, results):
        log.info('Analyzing strategy')

    strat.run()
