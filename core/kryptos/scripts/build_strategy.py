import json
import time
import requests
import os
from textwrap import dedent


from flask.helpers import get_debug_flag

import click
# from flask_jsonrpc.proxy import ServiceProxy
import pandas as pd
from rq import Queue

from kryptos.strategy import Strategy
from kryptos.data.manager import AVAILABLE_DATASETS
from kryptos import setup_logging
from kryptos.utils.outputs import in_docker
from kryptos.utils.load import get_strat
from kryptos.utils import tasks


REMOTE_API_URL = 'http://kryptos-205115.appspot.com/api'
LOCAL_API_URL = "http://web:8080/api"



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
@click.option("--python-script", "-p")
@click.option("--paper", is_flag=True, help="Run the strategy in Paper trading mode")
@click.option("--api", "-a", is_flag=True, help="Run the strategy via API")
@click.option("--worker", "-w", is_flag=True, help="Run the strategy inside an RQ worker")
@click.option("--hosted", "-h", is_flag=True, help="Run on a GCP instance via the API")
def run(market_indicators, machine_learning_models, dataset, columns, data_indicators, json_file, python_script, paper, api, worker, hosted):

    if api and worker:
        if not hosted:
            click.secho('Providing the `--worker` flag is not required when using the api', fg='yellow')
        else:
            click.echo('')


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

    if api or hosted:
        API_URL = LOCAL_API_URL
        if hosted:
            API_URL = REMOTE_API_URL

        run_from_api(strat, paper, API_URL)

    if worker:
        run_in_worker(strat, paper)

    else:
        viz = not in_docker()
        strat.run(live=paper, viz=viz)
        result_json = strat.quant_results.to_json()
        display_summary(result_json)


def display_summary(result_json):
    click.secho("\n\nResults:\n", fg="magenta")
    result_dict = json.loads(result_json)
    for k, v in result_dict.items():
        # nested dict with trading type as key
        metric, val = k, v["Backtest"]
        click.secho("{}: {}".format(metric, val), fg="green")

def run_from_api(strat, paper, api_url):
    if paper:
        q_name = 'paper'
    else:
        q_name = 'backtest'

    data = {
        'strat_json': json.dumps(strat.to_dict()),
        'queue_name': q_name
    }

    endpoint = os.path.join(api_url, 'strat')
    click.echo(f'Enqueuing strategy at {endpoint}')
    resp = requests.get(endpoint, json=data)
    click.echo(resp)
    resp.raise_for_status()
    data = resp.json()
    strat_id = data['strat_id']
    status = None
    click.echo(f'Strategy enqueued to job {strat_id}')
    click.secho(f'View the strat at http://0.0.0.0:8080/strategy/backtest/strategy/{strat_id}', fg='blue')

    while status not in ["finished", "failed"]:
        endpoint = os.path.join(api_url, 'monitor')
        resp = requests.get(endpoint, params={'strat_id': strat_id})
        data = resp.json()['strat_info']
        status, result, meta = data.get('status', ''), data.get('result', ''), data.get('meta', '')
        click.secho(status)
        click.secho(dedent(meta.get('output'))

        if result:
            click.secho(result)
            break
        time.sleep(3)


def run_in_worker(strat, paper):
    if paper:
        q_name = 'paper'
    else:
        q_name = 'backtest'
    q = Queue(q_name, connection=tasks.CONN)
    click.secho(f'Enqueuing strat on {q_name} queue', fg='cyan')
    #
    # # note that the strat.id will look different from app-created strategies
    job = q.enqueue(
        'worker.run_strat',
        job_id=strat.id,
        kwargs={
            'strat_json': json.dumps(strat.to_dict()),
            'strat_id': strat.id,
            'telegram_id': None,
            'live': paper,
            'simulate_orders': True
        },
        timeout=-1
    )

    click.secho(f'View the strat at http://0.0.0.0:8080/strategy/backtest/strategy/{strat.id}', fg='blue')

    while not job.is_finished:
        if job.is_failed:
            click.secho('job failed', fg='red')
            return
        click.secho(f'Status: {job.get_status()}')
        if job.meta:
            print(job.meta)
        time.sleep(3)

    display_summary(job.result)
