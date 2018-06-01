import click
from logbook import Logger

from kryptos.platform.utils import load, outputs, viz, algo
from kryptos.platform.settings import DEFAULT_CONFIG as CONFIG


log = Logger("Benchmark Runner")


@click.command()
@click.argument("strategy")
def benchmark(strategy):
    """Plots the percent return of a given algorithm against the benchmark of bitcoin price (btc_usdt)"""

    strat = load.load_by_name(strategy)
    click.echo("Benchmarking {}".format(strat.NAMESPACE))
    strat.CONFIG = CONFIG

    def initialize(context):
        algo.initialze_from_config(context)
        strat.initialize(context)

    def handle_data(context, data):
        algo.record_data(context, data)
        strat.trade_logic(context, data)

    def analyze(context, results):
        viz.plot_percent_return(results, strat.NAMESPACE)
        viz.plot_benchmark(results)
        output_file = outputs.get_output_file(strat, CONFIG) + ".csv"
        log.info("Dumping result csv to {}".format(output_file))
        viz.plot_buy_sells(results, pos=212)

    algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == "__main__":
    benchmark()
