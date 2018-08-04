import json
import redis
from rq import Queue, Connection, Worker
import click
import time
from flask import current_app

from app.models.user import StrategyModel
from app.extensions import db



QUEUE_NAMES = ['paper', 'live', 'backtest']


def get_conn():
    return redis.Redis(host=current_app.config['REDIS_HOST'], port=6379)

def get_queue(queue_name):
    return Queue(queue_name, connection=get_conn())

def queue_strat(strat_json, user_id=None, live=False, simulate_orders=True, depends_on=None):
    current_app.logger.debug(f'Queueing new strat with user_id {user_id}')
    strat_model = StrategyModel.from_json(strat_json, user_id=user_id)

    if live and simulate_orders:
        q = get_queue('paper')

    elif live:
        q = get_queue('live')

    else:
        q = get_queue('backtest')

    job = q.enqueue(
        'worker.run_strat',
        job_id=strat_model.uuid,
        kwargs={
            'strat_json': strat_json,
            'strat_id': strat_model.uuid,
            'live': live,
            'simulate_orders': simulate_orders
        },
        timeout=-1,
        depends_on=depends_on)

    if user_id is None:
        current_app.logger.warn('Not Saving Strategy to DB because no User specified')
        return job.id, q.name

    current_app.logger.info(f'Creating Strategy {strat_model.name} with user {user_id}')
    db.session.add(strat_model)
    db.session.commit()

    return job.id, q.name

def pretty_result(result_json):
    string = ''
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
        current_app.logger.info(f'Checking if strat in {q_name}')
        q = get_queue(q_name)
        job = q.fetch_job(strat_id)
        if job is not None:
            return job

    current_app.logger.error('Strategy not Found in Job')

def get_job_data(strat_id, queue_name=None):
    if queue_name is None:
        job = job_by_strat_id(strat_id)

    else:
        q = get_queue(queue_name)
        job = q.fetch_job(strat_id)

    if job is None:
        data = {'status': 'Not Found'}

    else:
        strat = StrategyModel.query.filter_by(uuid=strat_id).first()
        if strat is not None:
            strat.update_from_job(job)
        else:
            current_app.logger.warn("Fetching strat from RQ that is not in DB")
        data = {
            'status': job.status,
            'meta': job.meta,
            'started_at': job.started_at,
            'result': pretty_result(job.result)
        }

    return data
