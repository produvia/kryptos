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

host = 'redis' if in_docker() else 'localhost'
CONN = redis.Redis(host=host, port=6379)

log = logbook.Logger('WorkerManager')
logger_group.add_logger(log)

def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)


def run_strat(strat_json, strat_name, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy()
    strat.load_from_dict(strat_dict)
    strat.run(viz=False, live=live, simulate_orders=simulate_orders, as_job=True)
    result_df = strat.quant_results

    return result_df.to_json()


def queue_strat(strat_json, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy()
    strat.load_from_dict(strat_dict)

    if live and simulate_orders:
        q = get_queue('paper')

    elif live:
        q = get_queue('live')

    else:
        q = get_queue('backtest')

    job = q.enqueue(
        run_strat,
        job_id=strat.name,
        kwargs={
            'strat_json': strat_json,
            'strat_name': strat.name, # pass to keep same id as the job_id
            'live': live,
            'simulate_orders': simulate_orders
        },
        timeout=-1)

    return job.id, q.name


def workers_required():
    paper_q, live_q = get_queue('paper'), get_queue('live')
    total_queued = len(paper_q) + len(live_q)
    return total_queued



@click.command()
def manage_workers():
    # import before starting worker to loading during worker process
    # from kryptos.strategy import Strategy
    # from app.extensions import jsonrpc
    # from kryptos.utils.outputs import in_docker

    #start main worker
    with Connection(CONN):
        log.info('Starting initial workers')
        multiprocessing.Process(target=Worker(QUEUE_NAMES).work).start()

        # start seperate ingest worker
        multiprocessing.Process(target=Worker('ingest').work).start()


    # ingest data on start
    for ex in ['bitfinex', 'bittrex', 'poloniex']:
        run_ingest(ex)


    # create paper/live queues when needed
    while True:

        queue_names = ['paper', 'live']
        with Connection(CONN):
            if workers_required() > 0:
                log.info(f"{workers_required()} workers required")
                for i in range(workers_required()):
                    log.info("Creating live.paper worker")
                    multiprocessing.Process(target=Worker(queue_names).work, kwargs={'burst': True}).start()
            else:
                time.sleep(5)


def _ingest_exchange(exchange):
    exchange_bundle = ExchangeBundle(exchange)
    exchange_bundle.ingest(
        'daily',
        show_progress=True,
        show_breakdown=True,
        show_report=True
    )
    exchange_bundle.ingest(
        'minute',
        show_progress=True,
        show_breakdown=True,
        show_report=True
    )



def run_ingest(exchange):
    q = get_queue("ingest")
    log.error(f'Ingesting {exchange}')
    q.enqueue(_ingest_exchange, exchange)




if __name__ == '__main__':
    manage_workers()
