# -*- coding: utf-8 -*-
import json
from flask import Blueprint
from rq import Queue

from kryptos.platform.strategy import Strategy
from kryptos.server.extensions import jsonrpc
from kryptos.server.utils.worker import conn

# api blueprint currently not actually used
# jsonrpc acts as its own blueprint, asigning all method to api/
api = Blueprint("api", __name__, url_prefix="/api")


def queue_strat(strat_json):
    strat_dict = json.loads(strat_json)
    strat = Strategy()
    strat.load_from_dict(strat_dict)
    strat.run(viz=False)


@jsonrpc.method("Strat.run")
def run(strat_json):
    q = Queue(connection=conn)
    result = q.enqueue(queue_strat, strat_json)
    resp = {"status": "success", "data": {"strat_id": result.get_id()}}
    return resp


@jsonrpc.method("Strat.status")
def get_status(strat_id):
    q = Queue(connection=conn)
    job = q.fetch_job(strat_id)
    resp = {"status": job.status, "data": {"strat_id": job.get_id()}}
    return resp
