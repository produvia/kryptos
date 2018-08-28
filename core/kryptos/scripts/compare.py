import click
from logbook import Logger

from kryptos.utils import load, outputs, viz, algo
from kryptos.analysis import quant
from kryptos import add_logger
from kryptos.settings import METRICS, DEFAULT_CONFIG as CONFIG, TAConfig

log = Logger("Comparison")
add_logger(log)


@click.command()
@click.argument("strategies", nargs=-1)
@click.option("--metrics", "-m", multiple=True, default=None, help="Performance metrics")
def run(strategies, metrics):
    """Compares performance of provided algorithms

    \b
    Example:

        compare macdfix sma_crossover -m sharpe -m pnl

    \b
    Available example strategies:
      - bbands
      - bbands_psar
      - bear_market
      - buy_and_hodl
      - buy_low_sell_high
      - dual_moving_average
      - dynamic_rebalance
      - macdfix
      - mean_reversion_simple
      - obv
      - pugilist
      - rsi_profit_target
      - rsi_ta
      - sma_crossover
      - sma_macd
      - stoch_rsi
      - stochastics
    """

    click.secho(
        "Comparing Strategies: {}\nAnalyzing Metrics: {}".format(strategies, metrics), fg="white"
    )
    if len(metrics) > 0:
        CONFIG["METRICS"] = metrics
    else:
        CONFIG["METRICS"] = METRICS

    plot_name = "backtest-compare-"
    all_results = []
    for s in strategies:
        strat = load.load_by_name(s)
        strat.CONFIG = CONFIG
        plot_name += strat.NAMESPACE + "-"

        def initialize(context):
            algo.initialze_from_config(context)
            strat.initialize(context)
            # Set algo parameters as defined in settings.py
            param_values = [
                (attr, attr_val)
                for attr, attr_val in TAConfig().__class__.__dict__.items()
                if not attr.startswith("__")
            ]
            for param, val in param_values:
                setattr(context, param, val)

        def handle_data(context, data):
            algo.record_data(context, data)
            strat.trade_logic(context, data)

        def analyze(context, results):
            pos = viz.get_start_geo(len(CONFIG["METRICS"]) + 1)
            viz.plot_percent_return(results, name=strat.NAMESPACE, pos=pos)
            if strategies.index(s) == len(strategies) - 1:
                viz.plot_benchmark(results, pos=pos)
            pos += 1

            for m in CONFIG["METRICS"]:
                viz.plot_column(results, m, pos=pos, label=strat.NAMESPACE)
                pos += 1

            all_results.append((strat, context, results))

        algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.save_plot(CONFIG, plot_name)
    viz.show_plot()

    for strat, context, results in all_results:
        output_file = outputs.get_output_file(strat, CONFIG)
        log.info("Dumping result csv and pkl to {}".format(output_file))
        outputs.dump_to_csv(output_file, results)
        quant.dump_summary_table(strat.NAMESPACE, CONFIG, results)
        # Must be done outside of loop above to avoid matplotlib conflict
        quant.dump_plots_to_file(strat.NAMESPACE, results)


if __name__ == "__main__":
    run()