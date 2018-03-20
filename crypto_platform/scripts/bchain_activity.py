import click
import matplotlib.pyplot as plt
from logbook import Logger

from crypto_platform.utils import viz, algo
from crypto_platform.datasets.quandl_data.manager import QuandleDataManager


log = Logger('Blockchain Activity')


qdata = QuandleDataManager()


@click.command()
@click.option('--datasets', '-s', multiple=True)
def run(datasets):
    """Runs s strategy based on provided Blockchain dataset codes

        \b
        Example:
            bchain -s NTRAN -s CPTRA

        \b
        Available Dataset Codes:
          - TOTBC - Total Bitcoins
          - MKTCP - Bitcoin Market Capitalization
          - TRFEE - Bitcoin Total Transaction Fees
          - TRFUS - Bitcoin Total Transaction Fees USD
          - NETDF - Bitcoin Network Deficit
          - NTRAN - Bitcoin Number of Transactions
          - NTRAT - Bitcoin Total Number of Transactions
          - NTREP - Bitcoin Number of Transactions Excluding Popular Addresses
          - NADDU - Bitcoin Number of Unique Bitcoin Addresses Used
          - NTRBL - Bitcoin Number of Transaction per Block
          - TOUTV - Bitcoin Total Output Volume
          - ETRAV - Bitcoin Estimated Transaction Volume
          - ETRVU - Bitcoin Estimated Transaction Volume USD
          - TRVOU - Bitcoin USD Exchange Trade Volume
          - TVTVR - Bitcoin Trade Volume vs Transaction Volume Ratio
          - MKPRU - Bitcoin Market Price USD
          - CPTRV - Bitcoin Cost % of Transaction Volume
          - CPTRA - Bitcoin Cost Per Transaction
          - HRATE - Bitcoin Hash Rate
          - MIREV - Bitcoin Miners Revenue
          - ATRCT - Bitcoin Median Transaction Confirmation Time
          - BCDDC - Bitcoin Days Destroyed Cumulative
          - BCDDE - Bitcoin Days Destroyed
          - BCDDW - Bitcoin Days Destroyed (Minimum Age 1 Week)
          - BCDDM - Bitcoin Days Destroyed (Minimum Age 1 Month)
          - BCDDY - Bitcoin Days Destroyed (Minimum Age 1 Year)
          - BLCHS - Bitcoin api.blockchain Size
          - AVBLS - Bitcoin Average Block Size
          - MWTRV - Bitcoin My Wallet Transaction Volume
          - MWNUS - Bitcoin My Wallet Number of Users
          - MWNTD - Bitcoin My Wallet Number of Transaction Per Day
          - MIOPM - Bitcoin Mining Operating Margin
          - DIFF - Bitcoin Difficulty
  """

    click.secho('Executing using datasets:\n{}'.format(datasets), fg='white')

    def initialize(context):
        algo.initialze_from_config(context)

    def handle_data(context, data):
        algo.record_data(context, data)
        qdata.record_data(context, data, datasets)

    def analyze(context, results):
        pos = viz.get_start_geo(len(datasets))
        for d in datasets:
            name = qdata.pretty_title(d)
            viz.plot_column(results, d, pos=pos, y_label=name, label=name)
            pos += 1
        plt.legend()

    algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
