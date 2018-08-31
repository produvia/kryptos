# -*- coding: utf-8 -*-
import json
from flask import Blueprint, request, jsonify, current_app
import redis
from rq import Queue, Connection

from app import task


api = Blueprint("api", __name__, url_prefix="/api")


@api.route('/monitor', methods=['GET'])
def strat_status():
    strat_id = request.args['strat_id']
    queue_name = request.args.get('queue_name')

    current_app.logger.info(f'Fetching strat {strat_id} from {queue_name} queue')
    data = task.get_job_data(strat_id, queue_name)

    return jsonify(strat_info=data)

@api.route('/strat', methods=['POST', "GET"])
def run_strat():
    data = request.json
    current_app.logger.error(data)
    strat_dict = data.get('strat_json')
    queue_name = data.get('queue_name')

    live, simulate_orders = False, True
    if queue_name in ['paper', 'live']:
        live = True

    if queue_name == 'live':
        simulate_orders = False

    current_app.logger.info(f'Enqueuing strat to {queue_name} queue')
    job_id, _ = task.queue_strat(strat_dict, user_id=None, live=False, simulate_orders=True)
    current_app.logger.info(f"Strat running in job {job_id}")
    return jsonify(strat_id=job_id)
