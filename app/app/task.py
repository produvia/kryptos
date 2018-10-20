import os
import json
import redis
from rq import Queue, Connection, Worker
import click
import time
from flask import current_app

from app.models.user import StrategyModel, User
from app.extensions import db
from app.settings import get_from_datastore


QUEUE_NAMES = ["paper", "live", "backtest"]
REDIS_HOST, REDIS_PORT = os.getenv("REDIS_HOST"), os.getenv("REDIS_PORT")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or get_from_datastore("REDIS_PASSWORD", "production")

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


def get_queue(queue_name):
    current_app.logger.warn(f"Using Redis connection {REDIS_HOST}:{REDIS_PORT}")
    # if queue_name == 'ta':
    #     return Queue(queue_name, connection=CONN, async=False)
    return Queue(queue_name, connection=CONN)


def queue_strat(strat_json, user_id=None, live=False, simulate_orders=True, depends_on=None):
    current_app.logger.info(f"Queueing new strat with user_id {user_id}")
    strat_model = StrategyModel.from_json(strat_json, user_id=user_id)

    telegram_id = None
    if user_id is not None:
        user = User.query.get(user_id)
        telegram_id = user.telegram_id

    if live and simulate_orders:
        q = get_queue("paper")

    elif live:
        q = get_queue("live")

    else:
        q = get_queue("backtest")

    job = q.enqueue(
        "worker.run_strat",
        job_id=strat_model.uuid,
        kwargs={
            "strat_json": strat_json,
            "strat_id": strat_model.uuid,
            "telegram_id": telegram_id,  # allows worker to queue notfication w/o db
            "live": live,
            "user_id": user_id,
            "simulate_orders": simulate_orders,
        },
        timeout=-1,
        depends_on=depends_on,
    )

    if user_id is None:
        current_app.logger.warn("Not Saving Strategy to DB because no User specified")
        return job.id, q.name

    current_app.logger.info(f"Creating Strategy {strat_model.name} with user {user_id}")
    db.session.add(strat_model)
    db.session.commit()

    return job.id, q.name


def pretty_result(result_json):
    string = ""
    if result_json is None:
        return None
    result_dict = json.loads(result_json)
    for k, v in result_dict.items():
        # nested dict with trading type as key
        metric, val = k, v["Backtest"]
        string += f"{metric}: {val}\n"
    return string


def job_by_strat_id(strat_id):
    for q_name in QUEUE_NAMES:
        current_app.logger.info(f"Checking if strat in {q_name}")
        q = get_queue(q_name)
        job = q.fetch_job(strat_id)
        if job is not None:
            return job

    current_app.logger.error("Strategy not Found in Job")


def get_job_data(strat_id, queue_name=None):
    if queue_name is None:
        job = job_by_strat_id(strat_id)

    else:
        q = get_queue(queue_name)
        job = q.fetch_job(strat_id)

    if job is None:
        data = {"status": "Not Found"}

    else:
        strat = StrategyModel.query.filter_by(uuid=strat_id).first()
        if strat is not None:
            strat.update_from_job(job)
        else:
            current_app.logger.warn("Fetching strat from RQ that is not in DB")
        data = {
            "status": job.status,
            "meta": job.meta,
            "started_at": job.started_at,
            "result": pretty_result(job.result),
        }

    return data


def indicator_group_name_selectors() -> [(str, str)]:
    """Returns list of select options of indicator group names"""
    current_app.logger.debug("fetching ta-group-selects job")

    q = get_queue("ta")
    job_id = "ta-group-selects"
    job = q.fetch_job(job_id)
    if job is None:
        job = q.enqueue("worker.indicator_group_name_selectors", job_id=job_id, result_ttl=-1)
    return job.result


def all_indicator_selectors() -> [(str, str)]:
    """Returns the entire list of possible indicator abbreviation select options"""
    current_app.logger.debug("fetching ta-indicator-selects job")

    q = get_queue("ta")
    job_id = "ta-indicator-selects"
    job = q.fetch_job(job_id)
    if job is None:
        job = q.enqueue("worker.all_indicator_selectors", job_id=job_id, result_ttl=-1)
    return job.result


def _get_indicator_params(indicator_abbrev):
    current_app.logger.debug(f"fetching ta-indicator-params-{indicator_abbrev} job")

    q = get_queue("ta")
    job_id = f"ta-indicator-params-{indicator_abbrev}"
    job = q.fetch_job(job_id)
    if job is None:
        job = q.enqueue(
            "worker._get_indicator_params",
            job_id=job_id,
            kwargs={"indicator_abbrev": indicator_abbrev},
            result_ttl=-1,
        )
    return job.result


def get_indicators_by_group(group: str) -> [(str, str)]:
    """Returns list of select options containing abbreviations of the groups indicators"""
    current_app.logger.debug(f"fetching ta-indicator-by-group-{group} job")
    q = get_queue("ta")
    job_id = f"ta-indicator-by-group-{group}"
    job = q.fetch_job(job_id)
    if job is None:
        job = q.enqueue(
            "worker.get_indicators_by_group", job_id=job_id, kwargs={"group": group}, result_ttl=-1
        )
    return job.result


def queue_all_ta():
    current_app.logger.info("Queuing all ta-lib utils")
    groups = indicator_group_name_selectors()
    for g in groups:
        # dont block to wait for job complete,
        # will be ready when recalled to build strat
        indicators = get_indicators_by_group(g[0]) or []
        for i in indicators:
            _get_indicator_params(i[0])
    all_indicator_selectors()
