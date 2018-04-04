import click
# import matplotlib.pyplot as plt
from logbook import Logger

# from crypto_platform.utils import viz, algo
# from crypto_platform.datasets.quandl_data.manager import QuandleDataManager

from crypto_platform.strategy import Strategy


log = Logger('Blockchain Activity')


# qdata = QuandleDataManager()


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


    strat = Strategy()

    strat.use_dataset('quandl', columns=list(datasets))
    strat.run()



if __name__ == '__main__':
    run()
