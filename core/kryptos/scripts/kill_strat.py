import os
import json
import time
import requests

from flask.helpers import get_debug_flag

import click

# from flask_jsonrpc.proxy import ServiceProxy
import pandas as pd
from rq import Queue, Connection, Worker, get_failed_queue
from rq.job import Job
from kryptos.strategy import Strategy
from kryptos.data.manager import AVAILABLE_DATASETS
from kryptos import setup_logging
from kryptos.utils.outputs import in_docker
from kryptos.utils.load import get_strat
from kryptos.utils import tasks
from kryptos.scripts.build_strategy import run_from_api


REMOTE_API_URL = "http://kryptos.produvia.com/api"
LOCAL_API_URL = "http://web:5000/api" if in_docker() else "http://0.0.0.0:5000/api"

kill_key = "rq:jobs:kill"


class KillJob(Job):
    def kill(self):
        """ Force kills the current job causing it to fail """
        if self.is_started:
            self.connection.sadd(kill_key, self.get_id())

    def _execute(self):
        def check_kill(conn, id, interval=1):
            while True:
                res = conn.srem(kill_key, id)
                if res > 0:
                    raise Exception("KILLING")
                    os.kill(os.getpid(), signal.SIGINT)
                time.sleep(interval)

        t = Thread(target=check_kill, args=(self.connection, self.get_id()))
        t.start()
        log.warning("EXECUTING KILL JOB")
        return super()._execute()


class KillQueue(Queue):
    job_class = KillJob


class KillWorker(Worker):
    queue_class = KillQueue
    job_class = KillJob


@click.command()
@click.argument("strat_id", type=str)
def run(strat_id):
    click.secho(f"Killing strat {strat_id}", fg="yellow")

    marked = False
    job = None
    with Connection(tasks.CONN):
        for w in KillWorker.all():
            job = w.get_current_job()
            # q = None
            if job and job.id == strat_id:
                print(type(job))
                click.secho(f"Killing job with id: {job.id}")
                job.kill()
                # q = Queue(strat_job.origin)
                # click.secho("Marking for kill..")
                # job.meta["MARK_KILL"] = True
                # job.save_meta()
                # marked = True
                # click.secho("Marked job meta")
                # break

        if marked:
            while job.get_status() == "started":
                click.secho("Waiting for algo exit...")

                time.sleep(2)

            else:
                click.secho("Successfuly shut down job")

        else:
            click.secho("Did not find job")
