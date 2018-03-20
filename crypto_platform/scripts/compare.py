import click
from logbook import Logger

from crypto_platform.utils import load, outputs, viz, algo
from crypto_platform.config import CONFIG
from crypto_platform.analysis import quant

log = Logger('Comparison')


@click.command()
@click.argument('strategies', nargs=-1)
@click.option('--metrics', '-m', multiple=True, default=None, help='Performance metrics')
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

    click.secho('Comparing Strategies: {}\nAnalyzing Metrics: {}'.format(strategies, metrics), fg='white')
    if len(metrics) > 0:
        CONFIG.METRICS = metrics

    for s in strategies:
        strat = load.load_by_name(s)
        strat.CONFIG = CONFIG

        def initialize(context):
            algo.initialze_from_config(context)
            strat.initialize(context)

        def handle_data(context, data):
            algo.record_data(context, data)
            strat.trade_logic(context, data)

        def analyze(context, results):
            pos = viz.get_start_geo(len(CONFIG.METRICS) + 1)
            viz.plot_percent_return(results, name=strat.NAMESPACE, pos=pos)
            if strategies.index(s) == len(strategies) - 1:
                viz.plot_benchmark(results, pos=pos)
            pos += 1

            for m in CONFIG.METRICS:
                viz.plot_metric(results, m, pos=pos, label=strat.NAMESPACE)
                pos += 1

            output_file = outputs.get_output_file(strat, CONFIG) + '.csv'
            log.info('Dumping result csv to {}'.format(output_file))
            outputs.dump_to_csv(output_file, results)

            quant.build_summary_table(context, results)

        algo.run_algo(initialize, handle_data, analyze)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()
