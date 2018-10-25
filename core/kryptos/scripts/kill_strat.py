import os
import json
import time
import click

from rq import Connection
from kryptos.utils.outputs import in_docker
from kryptos.worker.worker import StratWorker
from kryptos.utils import tasks


REMOTE_API_URL = "http://kryptos.produvia.com/api"
LOCAL_API_URL = "http://web:5000/api" if in_docker() else "http://0.0.0.0:5000/api"


@click.command()
@click.argument("strat_id", type=str)
def run(strat_id):
    click.secho(f"Killing strat {strat_id}", fg="yellow")

    marked = False
    job = None
    with Connection(tasks.CONN):
        for w in StratWorker.all():
            job = w.get_current_job()
            # q = None
            if job and job.id == strat_id:
                print(type(job))
                click.secho(f"Killing job with id: {job.id}")
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
