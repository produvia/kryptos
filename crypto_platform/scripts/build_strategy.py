import click
import matplotlib.pyplot as plt
from logbook import Logger

from crypto_platform.strategy import Strategy
from crypto_platform.utils import viz, algo
from crypto_platform.config import CONFIG
from crypto_platform.datasets.google_trends.manager import GoogleTrendDataManager


log = Logger('Blockchain Activity')


@click.command()
@click.argument('indicators', nargs=-1)
@click.option('--dataset', '-d', help='Include asset in keyword list')
def run(indicators, dataset):

    strat = Strategy()

    for i in indicators:
        strat.add_indicator(i.upper())

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

