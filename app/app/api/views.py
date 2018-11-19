# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app

from app import task


api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/monitor", methods=["GET"])
def strat_status():
    strat_id = request.args["strat_id"]
    queue_name = request.args.get("queue_name")

    current_app.logger.info(f"Fetching strat {strat_id} from {queue_name} queue")
    data = task.get_job_data(strat_id, queue_name)

    return jsonify(strat_info=data)


@api.route("/strat", methods=["POST"])
def run_strat():
    data = request.json
    strat_dict = data.get("strat_json")
    queue_name = data.get("queue_name")
    user_uuid = data.get("user_uuid")

    live, simulate_orders = False, True
    if queue_name in ["paper", "live"]:
        live = True

    if queue_name == "live":
        simulate_orders = False

    current_app.logger.info(f"Enqueuing strat to {queue_name} queue")
    job_id, _ = task.queue_strat(
        strat_dict, user_uuid=user_uuid, live=live, simulate_orders=simulate_orders
    )
    current_app.logger.info(f"Strat running in job {job_id}")
    return jsonify(strat_id=job_id)


@api.route("/strat/delete", methods=["POST"])
def delete_strat():
    data = request.json
    strat_id = data.get("strat_id")
    if task.kill_strat(strat_id):
        return "Shutdown initiated", 200
    else:
        return "Could not shutdown", 409
