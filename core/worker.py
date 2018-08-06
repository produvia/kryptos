import os
import json
import redis
from rq import Queue, Connection, Worker
import click
import multiprocessing
import time
import logbook
from catalyst.exchange.exchange_bundle import ExchangeBundle

from kryptos import logger_group
from kryptos.strategy import Strategy
from kryptos.utils.outputs import in_docker
from kryptos.settings import QUEUE_NAMES


REDIS_HOST = os.getenv('REDIS_HOST', '10.138.0.4')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

log = logbook.Logger('WorkerManager')
logger_group.add_logger(log)
log.warn(f'Using Redis connection {REDIS_HOST}:{REDIS_PORT}')

def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)


def run_strat(strat_json, strat_id, telegram_id=None, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy.from_dict(strat_dict)
    strat.id = strat_id
    strat.telegram_id = telegram_id

    strat.run(viz=False, live=live, simulate_orders=simulate_orders, as_job=True)
    result_df = strat.quant_results

    return result_df.to_json()

def workers_required(queue_name):
    q = get_queue(queue_name)
    return len(q)



@click.command()
def manage_workers():
    # import before starting worker to loading during worker process
    # from kryptos.strategy import Strategy
    # from app.extensions import jsonrpc
    # from kryptos.utils.outputs import in_docker

    #start main worker
    with Connection(CONN):
        log.info('Starting initial workers')

        log.info('Starting worker for BACKTEST queue')
        multiprocessing.Process(target=Worker(['backtest'],).work).start()

        log.info('Starting worker for PAPER/LIVE queues')
        multiprocessing.Process(target=Worker(['paper', 'live']).work).start()




        # create paper/live queues when needed
        while True:
            for q in QUEUE_NAMES:
                required = workers_required(q)
                log.info(f"{required} workers required for {q}")
                for i in range(required):
                    log.info(f"Creating {q} worker")
                    multiprocessing.Process(target=Worker([q]).work, kwargs={'burst': True}).start()

            time.sleep(5)



if __name__ == '__main__':
    manage_workers()
