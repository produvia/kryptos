import os
import json
import time
import requests

from flask.helpers import get_debug_flag

import click

# from flask_jsonrpc.proxy import ServiceProxy
import pandas as pd
from rq import Queue, Connection, Worker, get_failed_queue

from kryptos.strategy import Strategy
from kryptos.data.manager import AVAILABLE_DATASETS
from kryptos import setup_logging
from kryptos.utils.outputs import in_docker
from kryptos.utils.load import get_strat
from kryptos.utils import tasks
from kryptos.scripts.build_strategy import run_from_api


REMOTE_API_URL = "http://kryptos.produvia.com/api"
LOCAL_API_URL = "http://web:5000/api" if in_docker() else "http://0.0.0.0:5000/api"


@click.command()
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
):
    click.secho(f"About to start {job_quantity} worker processes")

    if clean:
        with Connection(tasks.CONN):
            click.secho("Killing all exisiting jobs", fg="yellow")

            for q_name in ["live", "paper", "backtest"]:
                q = Queue(q_name)
                num_jobs = q.empty()
                click.echo("{0} jobs removed from {1} queue".format(num_jobs, q.name))

            for w in Worker.all():
                job = w.get_current_job()
                if job:
                    click.echo(f"cancelling job {job.id} from {job.origin}")
                    job.delete()

            for j in get_failed_queue().jobs:
                click.echo(f"cancelling job {j.id} from failed queue")
                j.delete()

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
            paper,
        )
        click.secho(f"Spawning strategy {i}")
        strat_id = run_from_api(strat, paper=True, live=False, hosted=True)
        strat_ids.append(strat_id)

    monitor_strats(strat_ids)
        # run_in_worker(strat, paper)


# TODO refactor the next two functions so they arent repeated in build_strategy.py and worker.py
def load_from_cli(
    market_indicators,
    machine_learning_models,
    dataset,
    columns,
    data_indicators,
    json_file,
    python_script,
    paper,
):
    strat = Strategy()

    if python_script is not None:
        strat = get_strat(python_script)

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
        strat.load_json_file(json_file)

    click.secho(strat.serialize(), fg="white")
    return strat


def display_summary(result_json):
    click.secho("\n\nResults:\n", fg="magenta")
    result_dict = json.loads(result_json)
    for k, v in result_dict.items():
        # nested dict with trading type as key
        metric, val = k, v["Backtest"]
        click.secho("{}: {}".format(metric, val), fg="green")


def run_from_api(strat, paper=False, live=False, hosted=False):
    click.secho("Running strat via API", fg="cyan")


    if paper:
        q_name = "paper"
    elif live:
        q_name = "live"
    else:
        q_name = "backtest"

    data = {"strat_json": json.dumps(strat.to_dict()), "queue_name": q_name}

    endpoint = os.path.join(REMOTE_API_URL, "strat")
    click.secho(f"Enqueuing strategy at {endpoint} on queue {q_name}", fg="yellow")

    resp = requests.post(endpoint, json=data)
    click.echo(resp)
    resp.raise_for_status()
    data = resp.json()
    strat_id = data["strat_id"]

    strat_url = get_strat_url(strat_id, REMOTE_API_URL, paper)
    click.echo(f"Strategy enqueued to job {strat_id}")
    click.secho(f"View the strat at {strat_url}", fg="blue")
    return strat_id


def monitor_strats(strat_ids):
    from itertools import cycle
    # from textwrap import dedent
    for i in cycle(strat_ids):
        endpoint = os.path.join(REMOTE_API_URL, "monitor")
        resp = requests.get(endpoint, params={"strat_id": i})
        data = resp.json()["strat_info"]

        status, result = data.get("status", ""), data.get("result", "")
        meta = data.get("meta", None)
        if status == "failed":
            click.secho(f"Strat: {i} has failed", fg='red')

        elif status == "finished":
            display_summary(result)

        else:
            click.echo(f'Strat {i}: {status}\n')

        time.sleep(3)
            # click.secho(dedent(meta.get("output", "")))


def get_strat_url(strat_id, base_url, paper):
    if paper:
        return os.path.join(base_url, "strategy/strategy", strat_id)
    return os.path.join(base_url, "strategy/backtest/strategy", strat_id)
