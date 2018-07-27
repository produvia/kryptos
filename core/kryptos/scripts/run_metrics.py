import click
from logbook import Logger

from kryptos.utils import load, viz, algo
from kryptos.settings import METRICS, DEFAULT_CONFIG as CONFIG


log = Logger("Benchmark Runner")


@click.command()
@click.argument("strategy")
@click.option("--metrics", "-m", multiple=True, default=None)
def run(strategy, metrics):
    """Plots the specified algo's performance metrics

    \b
    Example:
        metrics bbands -m sharpe -m pnl
    """

    if len(metrics) > 0:
        CONFIG["METRICS"] = metrics

    else:
        CONFIG["METRICS"] = METRICS

    strat = load.load_by_name(strategy)
    click.echo("Benchmarking {}".format(strat.NAMESPACE))
    strat.CONFIG = CONFIG

    def initialize(context):
        log.info(
            "Running {} using {} on {}".format(strat.NAMESPACE, CONFIG["ASSET"], CONFIG["EXCHANGE"])
        )
        algo.initialze_from_config(context)
        strat.initialize(context)

    def handle_data(context, data):
        algo.record_data(context, data)
        strat.trade_logic(context, data)

    def analyze(context, results):
        log.info("Analyzing {} with {}".format(strat.NAMESPACE, CONFIG["METRICS"]))
        pos = viz.get_start_geo(len(CONFIG["METRICS"]) + 1)
        for m in CONFIG["METRICS"]:
            viz.plot_column(results, m, pos, label=strat.NAMESPACE)
            pos += 1

    algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == "__main__":
    run()
