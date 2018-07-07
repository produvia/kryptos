# -*- coding: utf-8 -*-
import json
from flask import Blueprint
import redis
from rq import Queue, Connection

from kryptos.strategy import Strategy
from kryptos.app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.worker import worker

host = 'redis' if in_docker() else 'localhost'
conn = redis.Redis(host=host, port=6379)

# api blueprint currently not actually used
# jsonrpc acts as its own blueprint, asigning all method to api/
api = Blueprint("api", __name__, url_prefix="/api")


@jsonrpc.method("Strat.run")
def run(strat_json, live=False, simulate_orders=True):
    job_id, queue_name = worker.queue_strat(strat_json, live, simulate_orders)
    resp = {"status": "success", "data": {"strat_id": job_id, 'queue': queue_name}}
    return resp


@jsonrpc.method("Strat.status")
def get_status(strat_id, queue_name):
    q = worker.get_queue(queue_name)
    job = q.fetch_job(strat_id)
    resp = {"status": job.status, "data": {"strat_id": job.get_id()}}
    if job.is_finished:
        resp['strat_results'] = job.result
    return resp
