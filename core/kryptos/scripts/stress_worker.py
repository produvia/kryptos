import os
import json
import time
import requests

import click

from kryptos.data.manager import AVAILABLE_DATASETS
from kryptos.utils.outputs import in_docker
from kryptos.scripts.build_strategy import load_from_cli
from kryptos.scripts.kill_strat import kill_from_api


REMOTE_API_URL = "http://kryptos.produvia.com/api"
LOCAL_API_URL = "http://web:8080/api" if in_docker() else "http://0.0.0.0:8080/api"


@click.command(help="Launch multiple strategies")
@click.argument("job_quantity", type=int)
@click.option(
    "--market-indicators",
    "-ta",
    multiple=True,
    help="Market Indicators listed in order of priority",
)
@click.option("--machine-learning-models", "-ml", multiple=True, help="Machine Learning Models")
@click.option(
    "--dataset", "-d", type=click.Choice(AVAILABLE_DATASETS), help="Include asset in keyword list"
)
@click.option("--columns", "-c", multiple=True, help="Target columns for specified dataset")
@click.option("--data-indicators", "-i", multiple=True, help="Dataset indicators")
@click.option("--json-file", "-f")
@click.option("--python-script", "-p")
@click.option("--paper", is_flag=True, help="Run the strategy in Paper trading mode")
@click.option("--clean", is_flag=True, help="Kill all jobs before running")
@click.option("--hosted", "-h", is_flag=True, help="Run on a GCP instance via the API")
def run(
    job_quantity,
    market_indicators,
    machine_learning_models,
    dataset,
    columns,
    data_indicators,
    json_file,
    python_script,
    paper,
    clean,
    hosted,
):

    click.secho(f"About to start {job_quantity} worker processes")

    if hosted:
        click.secho("Running remotely", fg="yellow")
        api_url = REMOTE_API_URL
    else:
        click.secho("Running locally", fg="yellow")
        api_url = LOCAL_API_URL

    strat_ids = []

    for i in range(job_quantity):
        strat = load_from_cli(
            market_indicators,
            machine_learning_models,
            dataset,
            columns,
            data_indicators,
            json_file,
            python_script,
        )
        click.secho(f"Spawning strategy {i}")
        strat_id = start_from_api(strat, api_url, paper=paper, live=False, hosted=hosted)
        strat_ids.append(strat_id)

    try:
        monitor_strats(strat_ids, api_url)
    finally:
        clean_up(strat_ids, hosted)


def display_summary(result_json):
    click.secho("\n\nResults:\n", fg="magenta")
    result_dict = json.loads(result_json)
    for k, v in result_dict.items():
        # nested dict with trading type as key
        metric, val = k, v["Backtest"]
        click.secho("{}: {}".format(metric, val), fg="green")


def get_strat_url(strat_id, base_url, paper):
    if paper:
        return os.path.join(base_url, "strategy/strategy", strat_id)
    return os.path.join(base_url, "strategy/backtest/strategy", strat_id)


def clean_up(strat_ids, hosted):
    for i in strat_ids:
        kill_from_api(i, hosted)


def start_from_api(strat, api_url, paper=False, live=False, hosted=False):
    click.secho("Running strat via API", fg="cyan")

    if paper:
        q_name = "paper"
    elif live:
        q_name = "live"
    else:
        q_name = "backtest"

    data = {"strat_json": json.dumps(strat.to_dict()), "queue_name": q_name}

    endpoint = os.path.join(api_url, "strat")
    click.secho(f"Enqueuing strategy at {endpoint} on queue {q_name}", fg="yellow")

    resp = requests.post(endpoint, json=data)
    click.echo(resp)
    resp.raise_for_status()
    data = resp.json()
    strat_id = data["strat_id"]

    strat_url = get_strat_url(strat_id, api_url, paper)
    click.echo(f"Strategy enqueued to job {strat_id}")
    click.secho(f"View the strat at {strat_url}", fg="blue")
    return strat_id


def monitor_strats(strat_ids, api_url):
    from itertools import cycle

    # from textwrap import dedent
    for i in cycle(strat_ids):
        endpoint = os.path.join(api_url, "monitor")
        resp = requests.get(endpoint, params={"strat_id": i})
        data = resp.json()["strat_info"]

        status, result = data.get("status", ""), data.get("result", "")
        meta = data.get("meta", None)
        if status == "failed":
            click.secho(f"Strat: {i} has failed", fg="red")

        elif status == "finished":
            display_summary(result)

        else:
            click.echo(f"Strat {i}: {status}\n")

        time.sleep(3)
