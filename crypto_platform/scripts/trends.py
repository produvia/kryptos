import click
import matplotlib.pyplot as plt
from logbook import Logger


from crypto_platform.utils import viz, algo
from crypto_platform.config import CONFIG
from crypto_platform.datasets.google_trends.manager import GoogleTrendDataManager


log = Logger('Blockchain Activity')


@click.command()
@click.argument('keywords', nargs=-1)
@click.option('--asset', '-a', is_flag=True, help='Include asset in keyword list')
def run(keywords, asset):
    """Runs strategy using Google Search Trends

        Example:
            trends 'btc' 'btc usd' 'btc price'
    """

    keywords = list(keywords)
    if asset:
        keywords.append(CONFIG.ASSET.replace('_', ' '))
    trends = GoogleTrendDataManager(keywords)
    click.secho('Analysis Google Trends:\n{}'.format(keywords), fg='white')

    def initialize(context):
        algo.initialze_from_config(context)

    def handle_data(context, data):
        algo.record_data(context, data, trends)

    def analyze(context, results):
        viz.plot_column(results, 'price', pos=211, label='Price')
        for k in keywords:
            viz.plot_column(results, k, pos=212, y_label='Google Trends', label=k)
        plt.legend()

    algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
