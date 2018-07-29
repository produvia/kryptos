import click
from logbook import Logger

from kryptos.settings import DEFAULT_CONFIG as CONFIG
from kryptos.strategy import Strategy


log = Logger("Blockchain Activity")


@click.command()
@click.argument("keywords", nargs=-1)
@click.option("--asset", "-a", is_flag=True, help="Include asset in keyword list")
def run(keywords, asset):
    """Runs strategy using Google Search Trends

        Example:
            trends 'btc' 'btc usd' 'btc price'
    """

    keywords = list(keywords)
    if asset:
        keywords.append(CONFIG["ASSET"].replace("_", " "))

    strat = Strategy()
    strat.use_dataset("google", columns=keywords)

    click.secho("Analysis Google Trends:\n{}".format(keywords), fg="white")

    strat.run()


if __name__ == "__main__":
    run()
