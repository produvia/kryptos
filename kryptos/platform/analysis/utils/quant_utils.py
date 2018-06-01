import datetime
import pandas as pd

def log_error(err_file, err_msg):
    with open(err_file, "a") as f:
        f.write("-" * 15 + "\n")
        f.write(str(datetime.datetime.now()) + "\n")
        f.write(str(err_msg) + "\n")


def build_row_table(df, config=None, namespace=None):
    df_quant = pd.DataFrame(index=["Backtest"])

    df_quant["start_date"] = df.period_open.min().strftime("%Y-%m-%d")
    df_quant["end_date"] = df.period_open.max().strftime("%Y-%m-%d")
    df_quant["backtest_minutes"] = (
        (((df.period_open.max() - df.period_open.min()).seconds) / (60)) +
        (((df.period_open.max() - df.period_open.min()).seconds) / (60))
    )
    df_quant["backtest_days"] = (df.period_open.max() - df.period_open.min()).days + (
        ((df.period_open.max() - df.period_open.min()).seconds) / (3600 * 24)
    )
    df_quant["backtest_weeks"] = df_quant.backtest_days / 7
    ordered_trades = pd.DataFrame(
        [(t["dt"], t["price"], t["amount"]) for items in df.transactions.values for t in items],
        columns=["time", "price", "amount"],
    )
    df_quant["number_of_trades"] = int(len(ordered_trades) / 2)
    df_quant["average_trades_per_week_avg"] = float(df_quant.number_of_trades) / float(
        df_quant.backtest_weeks
    )
    if int(df_quant.number_of_trades):
        df_quant["average_trade_amount_usd"] = (
            ordered_trades.amount * ordered_trades.price
        ).abs().mean() / float(
            df_quant.number_of_trades
        )
    else:
        df_quant["average_trade_amount_usd"] = float("nan")

    df_quant["initial_capital"] = df.portfolio_value[0]
    df_quant["ending_capital"] = df.portfolio_value[-1]
    df_quant["net_profit"] = df_quant.ending_capital - df_quant.initial_capital
    df_quant["net_profit_pct"] = (
        df_quant.ending_capital - df_quant.initial_capital
    ) / df_quant.initial_capital * 100
    df_quant["average_daily_profit"] = df_quant.net_profit / df_quant.backtest_days
    df_quant["average_daily_profit_pct"] = df_quant.net_profit_pct / df_quant.backtest_days
    # df_quant['average_weekly_profit'] = df_quant.net_profit / df_quant.backtest_weeks
    # df_quant['average_weekly_profit_pct'] = df_quant.net_profit_pct / df_quant.backtest_weeks

    df_quant["average_exposure"] = df.starting_exposure.mean()
    df_quant["average_exposure_pct"] = (df.starting_exposure / df.portfolio_value).mean() * 100

    df_quant["net_risk_adjusted_return_pct"] = df_quant.net_profit / df_quant.average_exposure
    df_quant["max_drawdown_pct_catalyst"] = df.max_drawdown.min() * 100
    # Note: shifted series represents the previous day
    # Equivalent to (df.portfolio_value.diff()/df.portfolio_value.shift(1)).min()
    df_quant["max_daily_drawdown_pct"] = (
        (df.portfolio_value - df.portfolio_value.shift(1)) / df.portfolio_value.shift(1)
    ).min() * 100
    df_quant["max_weekly_drawdown_pct"] = (
        (df.portfolio_value - df.portfolio_value.shift(7)) / df.portfolio_value.shift(7)
    ).min() * 100
    # Note: removing first 30 samples of sharpe ratio
    df_quant["sharpe_ratio_avg"] = df.sharpe[30:].mean()
    df_quant["std_rolling_10_day_pct_avg"] = (
        df.portfolio_value.rolling(10).std() / df.portfolio_value
    ).mean()
    df_quant["std_rolling_100_day_pct_avg"] = (
        df.portfolio_value.rolling(100).std() / df.portfolio_value
    ).mean()

    df_quant["number_of_simulations"] = df.shape[0]

    if config:
        df_quant["data_freq"] = config['DATA_FREQ'] # minute / daily
        df_quant["asset"] = config['ASSET'] # btc_usd
        df_quant["exchange"] = config['EXCHANGE'] # poloniex
        df_quant["history_freq"] = config['HISTORY_FREQ'] # 1d
        # df_quant['input_params'] =

    if namespace:
        df_quant["namespace"] = namespace

    return df_quant
