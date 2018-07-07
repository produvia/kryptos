import os
import csv
import talib as ta
import click
from multiprocessing import Pool
import pandas as pd

from kryptos.strategy import Strategy
from kryptos.strategy.indicators import technical
from kryptos.settings import PERF_DIR
from kryptos.analysis.utils import quant_utils


RESULT_FILE = os.path.join(PERF_DIR, 'all_ta.csv')



def run_indicator(indicator_name):
    strat = Strategy(indicator_name)
    strat.add_market_indicator(indicator_name)
    click.secho('Running {}'.format(indicator_name), fg='cyan')
    strat.run(viz=False)
    click.secho('{}: {}'.format(indicator_name, strat.quant_results['net_profit_pct']), fg='cyan')
    # import pdb; pdb.set_trace()

    return strat


@click.command('run')
def run():
    all_ta = ta.get_functions()

    field_names = ['TA_INDICATOR', 'start_date', 'end_date', 'backtest_minutes', 'backtest_days',
       'backtest_weeks', 'number_of_trades', 'average_trades_per_week_avg',
       'average_trade_amount_usd', 'initial_capital', 'ending_capital',
       'net_profit', 'net_profit_pct', 'average_daily_profit',
       'average_daily_profit_pct', 'average_exposure', 'average_exposure_pct',
       'net_risk_adjusted_return_pct', 'max_drawdown_pct_catalyst',
       'max_daily_drawdown_pct', 'max_weekly_drawdown_pct', 'sharpe_ratio_avg',
       'std_rolling_10_day_pct_avg', 'std_rolling_100_day_pct_avg',
       'number_of_simulations']

    best_profit_pct = 0
    best_indicator = None


    with open(RESULT_FILE, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for i in all_ta:
            strat = run_indicator(i)
            result_dict = strat.quant_results.to_dict()

            profit_pct = result_dict['net_profit_pct']['Backtest']
            if profit_pct > best_profit_pct:
                best_profit_pct, best_indicator = profit_pct, i



            row = {'TA_INDICATOR': i}
            for k, v in result_dict.items():
                row[k] = v['Backtest']

                # nested dict with trading type as key
            writer.writerow(row)


        # df_results.append(strat.quant_results)

    click.secho('Best peforming indicator: {}'.format(best_indicator), fg='cyan')
    click.secho('Net Profit Percent: {}'.format(best_profit_pct), fg='cyan')

    #
    #
    # # Build the table
    # df_quant = pd.DataFrame()
    # for df in df_results:
    #     df = quant_utils.build_row_table(df['results'], strat.trading_info, strat.name)
    #     df_quant = df_quant.append(df, ignore_index=True)





    # pool = Pool(processes=4)
    # pool.map_async(run_indicator, ta.get_functions())




if __name__ == '__main__':
    run_all_ta()
