import os
import pandas as pd
import matplotlib.pyplot as plt

from logbook import Logger
from kryptos.platform.analysis.utils import quant_utils
from kryptos.platform.utils.outputs import get_algo_dir
from kryptos.platform import logger_group


log = Logger("QUANT")
logger_group.add_logger(log)


def dump_summary_table(namespace, config, df):
    if not isinstance(config, dict):
        config = config.__dict__

    ALGO_DIR = get_algo_dir(namespace)
    ERROR_FILE = os.path.join(ALGO_DIR, "errors.txt")

    log.debug("Completed Strategy with config:\n{}".format(config))
    log.info("Analyzing strategy performance")
    print("\n\n")
    log.info("Performance Result Columns:\n{}".format(df.columns))
    print("\n\n")

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
    df_quant = quant_utils.build_row_table(df)

    # Write to file
    f_path = os.path.join(ALGO_DIR, "backtest_summary.csv")
    with open(f_path, "w") as f:
        df_quant.T.to_csv(f)
        log.info("Wrote Summary Table to {}".format(f_path))


def dump_summary_table_all_strategies(config, list_dfs, output_dir):
    if not isinstance(config, dict):
        config = config.__dict__

    ALGO_DIR = get_algo_dir(output_dir)
    ERROR_FILE = os.path.join(ALGO_DIR, "errors.txt")

    log.debug("Completed strategies with config:\n{}".format(config))
    log.info("Analyzing strategies performance")
    print("\n\n")

    # Build the table
    df_quant = pd.DataFrame()
    for df in list_dfs:
        df = quant_utils.build_row_table(df['results'], config, df['namespace'])
        df_quant = df_quant.append(df, ignore_index=True)

    # Write to file
    f_path = os.path.join(ALGO_DIR, "backtest_summary.csv")
    with open(f_path, "w") as f:
        df_quant.to_csv(f)
        log.info("Wrote Summary Table All Strategies to {}".format(f_path))

    return df_quant


def dump_plots_to_file(namespace, df):
    log.info('Creating and dumping quant plots')
    algo_dir = get_algo_dir(namespace)
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
        SAVE_FOLDER,
    )
    dump_metric_plot(
        (df.portfolio_value - df.portfolio_value.shift(7)) / df.portfolio_value.shift(7) * 100,
        "Max Weekly Drawdown %",
        SAVE_FOLDER,
    )

    log.info("Saved plots to {}".format(SAVE_FOLDER))


def dump_metric_plot(metric, metric_name, save_folder):
    ax = metric.plot(legend=metric_name)
    f_name = metric_name.replace(" ", "_") + ".png"
    f_path = os.path.join(save_folder, f_name)
    plt.savefig(f_path, bbox_inches="tight", dpi=300)
    plt.close()
