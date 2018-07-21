# -*- coding: utf-8 -*-
import json
from flask import Blueprint, request, jsonify, current_app
import redis
from rq import Queue, Connection

from kryptos.strategy import Strategy
from app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.worker import worker
from kryptos.settings import QUEUE_NAMES

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

    resp = {"status": job.status, "data": {"strat_id": job.get_id(), "meta": job.meta}}
    if job.is_finished:
        resp['strat_results'] = job.result
    return resp



@api.route('/submit', methods=['POST'])
def run_strat():
    strat_dict = request.json
    trade_type = strat_dict['trade_type']
    live = trade_type in ['live', 'paper']
    simulate_orders = trade_type == 'live'

    job_id, queue_name = worker.queue_strat(json.dumps(strat_dict), live, simulate_orders)
    return jsonify(job_id=job_id)

def pretty_result(result_json):
    string = ''
    result_dict = json.loads(result_json)
    for k, v in result_dict.items():
        # nested dict with trading type as key
        metric, val = k, v["Backtest"]
        string += f"{metric}: {val}\n"
    return string


@api.route('/monitor', methods=['GET'])
def strat_status():
    strat_id = request.args['strat_id']
    queue_name = request.args.get('queue_name')

    current_app.logger.info(f'Fetching strat {strat_id} from {queue_name} queue')
    if queue_name is None:
        for q_name in QUEUE_NAMES:
            current_app.logger.info(f'Checking if strat in {q_name}')
            q = worker.get_queue(q_name)
            job = q.fetch_job(strat_id)
            if job is not None:
                break
    else:
        q = worker.get_queue(queue_name)
        job = q.fetch_job(strat_id)

    if job is None:
        data = {'status': 'Not Found'}

    else:
        data = {
            'status': job.status,
            'meta': job.meta,
            'started_at': job.started_at,
            'result': pretty_result(job.result)
        }

    return jsonify(strat_info=data)
