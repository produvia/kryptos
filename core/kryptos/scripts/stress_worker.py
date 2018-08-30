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


REMOTE_API_URL = 'http://kryptos.produvia.com/api'
LOCAL_API_URL = "http://web:5000/api" if in_docker() else 'http://0.0.0.0:5000/api'



@click.command()
@click.argument('job_quantity', type=int)
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
@click.option("--clean", is_flag=True, help='Kill all jobs before running')
def run(job_quantity, market_indicators, machine_learning_models, dataset, columns, data_indicators, json_file, python_script, paper, clean):
    click.secho(f'About to start {job_quantity} worker processes')

    remove_zombie_workers()

    if clean:
        with Connection(tasks.CONN):
            click.secho('Killing all exisiting jobs', fg='yellow')

            for q_name in ['live', 'paper', 'backtest']:
                q = Queue(q_name)
                num_jobs = q.empty()
                click.echo('{0} jobs removed from {1} queue'.format(num_jobs, q.name))

            for w in Worker.all():
                job = w.get_current_job()
                if job:
                    click.echo(f'cancelling job {job.id} from {job.origin}')
                    job.delete()

            for j in get_failed_queue().jobs:
                click.echo(f'cancelling job {j.id} from failed queue')
                j.delete()

    for i in range(job_quantity):
        strat = load_from_cli(market_indicators, machine_learning_models, dataset, columns, data_indicators, json_file, python_script, paper)
        click.secho(f'Spawning strategy {i}')
        run_in_worker(strat, paper)


# TODO refactor the next two functions so they arent repeated in build_strategy.py and worker.py
def load_from_cli(market_indicators, machine_learning_models, dataset, columns, data_indicators, json_file, python_script, paper):
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


def remove_zombie_workers():
    click.secho('Removing zombie workers', fg='yellow')
    workers = Worker.all(connection=tasks.CONN)
    for worker in workers:
        if len(worker.queues) < 1:
            click.secho(f"{worker} is a zombie, killing...", fg='red')
            job = worker.get_current_job()
            if job is not None:
                job.ended_at = datetime.datetime.utcnow()
                worker.failed_queue.quarantine(job, exc_info=("Dead worker", "Moving job to failed queue"))
            worker.register_death()

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
    return job
