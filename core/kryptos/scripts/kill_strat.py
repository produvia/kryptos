import os
import json
import time
import click
import requests

from rq import Connection
from kryptos.utils.outputs import in_docker
from kryptos.worker.worker import StratWorker
from kryptos.utils import tasks


REMOTE_BASE_URL = "https://kryptos-205115.appspot.com"
LOCAL_BASE_URL = "http://web:8080"


@click.command()
@click.argument("strat_id", type=str)
@click.option("--api", "-a", is_flag=True, help="Run the strategy via API")
@click.option("--hosted", "-h", is_flag=True, help="Run on a GCP instance via the API")
# @click.option("--hosted", "-h", is_flag=True, help="Kill on a GCP instance via the API")


def run(strat_id, api, hosted):
    click.secho(f"Killing strat {strat_id}", fg="yellow")

    marked = False
    job = None

    if api or hosted:
        kill_from_api(strat_id, hosted=hosted)
        return

    with Connection(tasks.CONN):
        for w in StratWorker.all():
            job = w.get_current_job()
            if job and job.id == strat_id:
                job.kill()
                marked = True
                break

        if marked:
            while job.get_status() == "started":
                click.secho("Waiting for algo exit...")
                click.secho(f"Status: {job.get_status()}")
                time.sleep(2)

            else:
                click.secho("Successfuly shut down job")

        else:
            click.secho("Did not find job")


def kill_from_api(strat_id, hosted=False):
    click.secho("Killing strat via API", fg="cyan")
    if hosted:
        click.secho("Running remotely", fg="yellow")
        base_url = REMOTE_BASE_URL
    else:
        click.secho("Running locally", fg="yellow")
        base_url = LOCAL_BASE_URL

    api_url = os.path.join(base_url, "api")

    data = {"strat_id": strat_id}

    endpoint = os.path.join(api_url, "strat/delete")
    click.secho(f"Killing strat {strat_id} at {endpoint}", fg="yellow")

    resp = requests.post(endpoint, json=data)
    click.echo(resp)
    resp.raise_for_status()
