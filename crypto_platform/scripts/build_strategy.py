import click
import matplotlib.pyplot as plt
from logbook import Logger

from crypto_platform.strategy import Strategy
from crypto_platform.utils import viz, algo
from crypto_platform.config import CONFIG
from crypto_platform.datasets.google_trends.manager import GoogleTrendDataManager


log = Logger('Blockchain Activity')


@click.command()
@click.option('--indicators', '-i', multiple=True, help='Indicators listed in order of priority')
@click.option('--dataset', '-d', help='Include asset in keyword list')
@click.option('--columns', '-c', multiple=True, help='Target columns for specified dataset')
def run(indicators, dataset, columns):
    click.secho('''
        Creating Trading Strategy:
        Indicators: {}
        Dataset: {}
        Dataset Columns: {}
        '''.format(indicators, dataset, columns), fg='white')

    strat = Strategy()

    columns = list(columns)

    for i in indicators:
        strat.add_indicator(i.upper())

    if dataset is not None:
        strat.use_dataset(dataset, columns)

    @strat.init
    def initialize(context):
        log.info('Initializing strategy')

    @strat.handle_data
    def handle_data(context, data):
        log.info('Doing extra stuff for handling data')

    @strat.analyze
    def analyze(context, results):
        log.info('Analyzing strategy')
        # viz.plot_metric(results, 'price', pos=211, label='Price')

    strat.run()
