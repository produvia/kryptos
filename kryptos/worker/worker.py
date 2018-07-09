import json
import redis
from rq import Queue, Connection, Worker
import click
import multiprocessing
import time

from kryptos.strategy import Strategy
from kryptos.app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.settings import QUEUE_NAMES

host = 'redis' if in_docker() else 'localhost'
CONN = redis.Redis(host=host, port=6379)



def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)


def run_strat(strat_json, live=False, simulate_orders=True):
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
        q = get_queue('live')

    elif live:
        q = get_queue('paper')

    else:
        q = get_queue('backtest')


    job = q.enqueue(run_strat, job_id=strat.name, kwargs={'strat_json': strat_json, 'live': live, 'simulate_orders': simulate_orders}, timeout=-1)

    return job.id, q.name

def get_strat_data(strat_name, queue_name):
    q = get_queue(queue_name)

    job = q.fetch_job(strat_name)
    if job is None:
        return

    if job.is_failed:
        info = job.exc_info.strip().split('\n')[-1]
        raise Exception('Strat job failed: {}'.format(info))

    if job.result is None:
        return job.meta

    return job.result, job.meta

def workers_required():
    paper_q, live_q = get_queue('paper'), get_queue('live')
    total_queued = len(paper_q) + len(live_q)
    return total_queued



@click.command()
def manage_workers():
    # import before starting worker to loading during worker process
    # from kryptos.strategy import Strategy
    # from kryptos.app.extensions import jsonrpc
    # from kryptos.utils.outputs import in_docker

    #start main worker
    with Connection(CONN):
        multiprocessing.Process(target=Worker(QUEUE_NAMES).work).start()

    # create live queus when needed
    while True:
        queue_names = ['paper', 'live']
        with Connection(CONN):
            if workers_required() > 0:
                for i in range(workers_required()):
                    multiprocessing.Process(target=Worker(queue_names).work, kwargs={'burst': True}).start()
            else:
                time.sleep(5)

if __name__ == '__main__':
    manage_workers()
