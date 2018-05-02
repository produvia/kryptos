# -*- coding: utf-8 -*-
import json
from flask import Blueprint, Response
from rq import Queue, Connection

from kryptos.platform.strategy import Strategy
from kryptos.server.extensions import jsonrpc
from kryptos.server.utils.worker import conn


api = Blueprint("api", __name__)


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
