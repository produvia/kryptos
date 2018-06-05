import json
import time
import requests

from flask.helpers import get_debug_flag

import click
import logbook
from flask_jsonrpc.proxy import ServiceProxy

from kryptos.platform.strategy import Strategy
from kryptos.platform.data.manager import AVAILABLE_DATASETS
from kryptos.platform import setup_logging

from kryptos.app.settings import DevConfig, ProdConfig


log = logbook.Logger("Platform")
setup_logging()


@click.command()
@click.option(
    "--market-indicators",
    "-ta",
    multiple=True,
    help="Market Indicators listed in order of priority",
)
@click.option(
    "--machine-learning-models",
    "-ml",
    multiple=True,
    help="Machine Learning Models",
)
@click.option(
    "--dataset", "-d", type=click.Choice(AVAILABLE_DATASETS), help="Include asset in keyword list"
)
@click.option("--columns", "-c", multiple=True, help="Target columns for specified dataset")
@click.option("--data-indicators", "-i", multiple=True, help="Dataset indicators")
@click.option("--json-file", "-f")
@click.option("--paper", is_flag=True, help="Run the strategy in Paper trading mode")
@click.option("--rpc", is_flag=True, help="Run the strategy via JSONRPC")
@click.option("--hosted", "-h", is_flag=True, help="Run via rpc using remote server")

def run(market_indicators, machine_learning_models, dataset, columns, data_indicators, json_file, paper, rpc, hosted):

    strat = Strategy()

    columns = list(columns)

    for i in market_indicators:
        strat.add_market_indicator(i.upper())

    for i in machine_learning_models:
        strat.add_ml_models(i.upper())

    # currently assigns -i indicator to the column provided at the same index
    if dataset is not None:
        strat.use_dataset(dataset, columns)
        for i, ind in enumerate(data_indicators):
            strat.add_data_indicator(dataset, ind.upper(), col=columns[i])

    if json_file is not None:
        strat.load_from_json(json_file)

    @strat.init
    def initialize(context):
        log.info("Initializing strategy")
        pass

    @strat.handle_data
    def handle_data(context, data):
        # log.debug('Doing extra stuff for handling data')
        pass

    @strat.analyze()
    def analyze(context, results, pos):
        log.info("Analyzing strategy")
        pass

    click.secho(strat.serialize(), fg="white")

    if rpc:
        CONFIG = DevConfig if get_debug_flag() else ProdConfig

        if hosted:
            CONFIG = ProdConfig  # to run on remote during dev

        strat_id = run_rpc(strat, CONFIG.API_URL)
        poll_status(strat_id, CONFIG.API_URL)

    else:
        strat.run(live=paper)


def run_rpc(strat, api_url):
    click.secho(
        """
        *************
        Running strategy on JSONRPC server at {}
        Visualization will not be shown.
        *************
        """.format(
            api_url
        ),
        fg="yellow",
    )
    rpc_service = ServiceProxy(api_url)
    strat_json = strat.serialize()
    res = rpc_service.Strat.run(strat_json)
    log.info(res)

    if res.get("error"):
        raise Exception(res["error"])

    result = res["result"]
    strat_id = result["data"]["strat_id"]
    status = result["status"]
    click.secho("Job Started. Strategy job ID: {}".format(strat_id))
    click.secho("status: {}".format(status), fg="magenta")
    return strat_id


def poll_status(strat_id, api_url):
    rpc_service = ServiceProxy(api_url)
    status = None
    colors = {"started": "green", "failed": "red", "finished": "blue"}
    while status not in ["finished", "failed"]:
        res = rpc_service.Strat.status(strat_id)
        status = res["result"]["status"]
        click.secho("status: {}".format(status), fg=colors.get(status))
        time.sleep(2)
