import json
import time
import requests
import os
from textwrap import dedent

import click
from rq import Queue

from kryptos.strategy import Strategy
from kryptos.data.manager import AVAILABLE_DATASETS
from kryptos.utils.outputs import in_docker
from kryptos.utils.load import get_strat
from kryptos.utils import tasks
from kryptos.settings import REMOTE_BASE_URL, LOCAL_BASE_URL


@click.command(name="build", help="Launch a strategy")
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
@click.option("--live", is_flag=True, help="Run the strategy in Paper trading mode")
@click.option("--api", "-a", is_flag=True, help="Run the strategy via API")
@click.option("--worker", "-w", is_flag=True, help="Run the strategy inside an RQ worker")
@click.option("--hosted", "-h", is_flag=True, help="Run on a GCP instance via the API")
def run(
    market_indicators,
    machine_learning_models,
    dataset,
    columns,
    data_indicators,
    json_file,
    python_script,
    paper,
    live,
    api,
    worker,
    hosted,
):
    if api and worker:
        if not hosted:
            click.secho(
                "Providing the `--worker` flag is not required when using the api", fg="yellow"
            )
        else:
            click.echo("")

    strat = load_from_cli(
        market_indicators,
        machine_learning_models,
        dataset,
        columns,
        data_indicators,
        json_file,
        python_script,
    )

    click.secho(f"Running in Paper mode: {paper}", fg="yellow")

    if api or hosted:
        run_from_api(strat, paper=paper, live=live, hosted=hosted)
        return

    elif worker:
        run_in_worker(strat, paper=paper, live=live)
        return

    else:
        click.secho(
            "Running locally w/o worker (ML still requires a worker process)", fg="cyan")
        viz = not in_docker()
        strat.run(live=paper or live, viz=viz,
                  simulate_orders=not live, user_id=1)
        result_json = strat.quant_results.to_json()
        display_summary(result_json)


def load_from_cli(
    market_indicators,
    machine_learning_models,
    dataset,
    columns,
    data_indicators,
    json_file,
    python_script,
):
    strat = Strategy()

    if python_script is not None:
        strat = get_strat(python_script)

    columns = list(columns)

    for i in market_indicators:
        click.echo(f"Attaching indicator: {i.upper()}")
        strat.add_market_indicator(i.upper())

    for i in machine_learning_models:
        click.echo(f"Attaching ml model: {i.upper()}")
        strat.add_ml_models(i.upper())

    # currently assigns -i indicator to the column provided at the same index
    if dataset is not None:
        click.echo(f"Using dataset: {dataset}")
        strat.use_dataset(dataset, columns)
        for i, ind in enumerate(data_indicators):
            strat.add_data_indicator(dataset, ind.upper(), col=columns[i])

    if json_file is not None:
        click.echo(f"Loading from json file {json_file}")
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
    if hosted:
        click.secho("Running remotely", fg="yellow")
        base_url = REMOTE_BASE_URL
    else:
        click.secho("Running locally", fg="yellow")
        base_url = LOCAL_BASE_URL

    api_url = os.path.join(base_url, "api")

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
    status = None

    strat_url = get_strat_url(strat_id, base_url)
    click.echo(f"Strategy enqueued to job {strat_id}")
    click.secho(f"View the strat at {strat_url}", fg="blue")

    while status not in ["finished", "failed"]:
        endpoint = os.path.join(api_url, "monitor")
        resp = requests.get(endpoint, params={"strat_id": strat_id})
        data = resp.json()["strat_info"]
        status, result, meta = (
            data.get("status", ""),
            data.get("result", ""),
            data.get("meta", None),
        )
        click.secho(status)
        if meta:
            click.secho(dedent(meta.get("output", "")))

        if result:
            click.secho(result)
            break
        time.sleep(3)


def get_strat_url(strat_id, base_url):
    return os.path.join(base_url, "strategy", strat_id)


def run_in_worker(strat, paper=False, live=False):
    click.secho("Running local strategy using worker", fg="cyan")
    if paper:
        q_name = "paper"
    elif live:
        q_name = "live"
    else:
        q_name = "backtest"
    q = Queue(q_name, connection=tasks.CONN)
    click.secho(f"Enqueuing strat on {q_name} queue", fg="cyan")
    #
    # # note that the strat.id will look different from app-created strategies
    job = q.enqueue(
        "kryptos.worker.run_strat",
        job_id=strat.id,
        kwargs={
            "strat_json": json.dumps(strat.to_dict()),
            "strat_id": strat.id,
            "telegram_id": None,
            "live": paper or live,
            "simulate_orders": not live,
            "user_id": 1
        },
        timeout=-1,
    )

    strat_url = get_strat_url(strat.id, LOCAL_BASE_URL)
    click.secho(f"View the strat at {strat_url}", fg="blue")

    while not job.is_finished:
        if job.is_failed:
            click.secho("job failed", fg="red")
            return
        click.secho(f"Status: {job.get_status()}")
        if job.meta:
            print(job.meta)
        time.sleep(3)

    display_summary(job.result)
