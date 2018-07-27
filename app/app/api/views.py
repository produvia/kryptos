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
