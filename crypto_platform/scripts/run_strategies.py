""" This script simply runs each algorithim within algos/single_asset/
The recorded results are saved to a csv file  and as a pickled pandas Dataframe
in scripts/performance_results
"""

from logbook import Logger
from crypto_platform.utils import load, outputs, viz, algo
from crypto_platform.settings import DEFAULT_CONFIG as CONFIG


import click

log = Logger("Strategy Runner")


@click.command()
def run():
    """Runs all the example algorithms inside /crypo_platform/algos

    Plots the portfolio value over time for each strategy
    """
    for strategy in load.load_algos():
        if strategy is None:
            continue

        log.info("Running {}".format(strategy.NAMESPACE))
        strategy.CONFIG = CONFIG

        def initialize(context):
            algo.initialze_from_config(context)
            strategy.initialize(context)

        def handle_data(context, data):
            algo.record_data(context, data)
            strategy.trade_logic(context, data)

        def analyze(context, results):
            viz.plot_portfolio(context, results, strategy.NAMESPACE)
            output_file = outputs.get_output_file(strategy, CONFIG) + ".csv"
            log.info("Dumping result csv to {}".format(output_file))
            outputs.dump_to_csv(output_file, results)

        algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == "__main__":
    run()
