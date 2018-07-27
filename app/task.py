import json
import redis
from rq import Queue, Connection, Worker
import click
import time
import logbook
from flask import current_app


CONN = redis.Redis(host=current_app.config['REDIS_HOST'], port=6379)

def get_queue(queue_name):
    return Queue(queue_name, connection=CONN)

def queue_strat(strat_json, user_id, live=False, simulate_orders=True, depends_on=None):
    strat_model = StrategyModel.from_json(strat_json)

    if live and simulate_orders:
        q = get_queue('paper')

    elif live:
        q = get_queue('live')

    else:
        q = get_queue('backtest')

    job = q.enqueue(
        'worker.run_strat',
        job_id=strat_model.id,
        kwargs={
            'strat_json': strat_json,
            'live': live,
            'simulate_orders': simulate_orders
        },
        timeout=-1,
        depends_on=depends_on)

    if user_id is None:
        log.warn('Not Saving Strategy to DB because no User specified')
        return job.id, q.name

    log.info(f'Creating Strategy {strat_model.name} with user {user_id}')
    db.session.add(strat_model)
    db.session.commit()

    return job.id, q.name
