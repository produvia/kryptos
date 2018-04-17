import os
import pandas as pd
import matplotlib.pyplot as plt

from crypto_platform.analysis.utils import quant_utils
from crypto_platform.utils.outputs import get_algo_dir


def dump_summary_table(namespace, config, df):
    if not isinstance(config, dict):
        config = config.__dict__

    ALGO_DIR = get_algo_dir(namespace, config)
    ERROR_FILE = os.path.join(ALGO_DIR, "errors.txt")

    print("\n" * 5)
    print(config)
    print("\n" * 5)
    print(df.columns)
    print("\n" * 5)

    try:
        # No missing days in index
        if config["DATA_FREQ"] == "daily":
            assert (pd.date_range(start=df.index.min(), periods=len(df)) == df.index).all()

        # There should be no missing data
        # Note: we expect some missing data in the first row(s)
        assert df.iloc[1:].isnull().sum().sum() == 0

        # Starting capital should be consistent with config
        assert config["CAPITAL_BASE"] == df.portfolio_value[0]

    except Exception as e:
        quant_utils.log_error(ERROR_FILE, e)

    # Build the table
    df_quant = pd.DataFrame(index=["Backtest"])

    df_quant["start_date"] = df.period_open.min().strftime("%Y-%m-%d")
    df_quant["end_date"] = df.period_open.max().strftime("%Y-%m-%d")
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

    # Write to file
    f_path = os.path.join(ALGO_DIR, "backtest_summary.csv")
    with open(f_path, "w") as f:
        df_quant.to_csv(f)


def dump_plots_to_file(namespace, config, df):
    if not isinstance(config, dict):
        config = config.__dict__

    algo_dir = get_algo_dir(namespace, config)
    SAVE_FOLDER = os.path.join(algo_dir, "figures")
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    plt.rcParams["figure.figsize"] = (6, 4)
    plt.rcParams["axes.labelpad"] = 10
    plt.style.use("ggplot")
    dump_metric_plot(df.portfolio_value, "Portfolio USD", SAVE_FOLDER)
    dump_metric_plot(df.cash, "Cash", SAVE_FOLDER)
    dump_metric_plot(
        pd.DataFrame(
            [(t["dt"], t["amount"]) for t_list in df.transactions for t in t_list]
        ).set_index(
            0
        ),
        "Trades",
        SAVE_FOLDER,
    )
    dump_metric_plot(df.price, "Asset Price USD", SAVE_FOLDER)
    dump_metric_plot(df.pnl, "PnL", SAVE_FOLDER)
    dump_metric_plot(df.pnl / df.portfolio_value, "PnL %", SAVE_FOLDER)
    dump_metric_plot(df.sharpe, "Sharpe Ratio", SAVE_FOLDER)
    dump_metric_plot(df.sharpe[30:], "Sharpe Ratio (head-cutoff)", SAVE_FOLDER)
    dump_metric_plot(df.sortino, "Sortino Ratio", SAVE_FOLDER)
    dump_metric_plot(df.sortino[30:], "Sortino Ratio (head-cutoff)", SAVE_FOLDER)
    dump_metric_plot(df.beta, "Beta", SAVE_FOLDER)
    dump_metric_plot(df.beta[30:], "Beta (head-cutoff)", SAVE_FOLDER)
    dump_metric_plot(df.alpha, "Alpha", SAVE_FOLDER)
    dump_metric_plot(df.alpha[30:], "Alpha (head-cutoff)", SAVE_FOLDER)
    dump_metric_plot(df.starting_exposure, "Exposure USD", SAVE_FOLDER)
    dump_metric_plot(
        df.portfolio_value.rolling(10).std() / df.portfolio_value,
        "Standard Deviation % (10-day)",
        SAVE_FOLDER,
    )
    dump_metric_plot(
        df.portfolio_value.rolling(100).std() / df.portfolio_value,
        "Standard Deviation % (100-day)",
        SAVE_FOLDER,
    )
    dump_metric_plot(
        (df.portfolio_value - df.portfolio_value.shift(1)) / df.portfolio_value.shift(1) * 100,
        "Max Daily Drawdown %",
        SAVE_FOLDER
    )
    dump_metric_plot(
        (df.portfolio_value - df.portfolio_value.shift(7)) / df.portfolio_value.shift(7) * 100,
        "Max Weekly Drawdown %",
        SAVE_FOLDER
    )


def dump_metric_plot(metric, metric_name, save_folder):
    plt.close()
    ax = metric.plot(legend=metric_name)
    f_name = metric_name.replace(" ", "_") + ".png"
    f_path = os.path.join(save_folder, f_name)
    plt.savefig(f_path, bbox_inches="tight", dpi=300)
