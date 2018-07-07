import json
import redis
from rq import Queue, Connection, Worker

from kryptos.strategy import Strategy
from kryptos.app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.settings import QUEUE_NAMES

host = 'redis' if in_docker() else 'localhost'
CONN = redis.Redis(host=host, port=6379)



def start_worker():
    # import before starting worker to loading during worker process
    from kryptos.strategy import Strategy
    from kryptos.app.extensions import jsonrpc
    from kryptos.utils.outputs import in_docker

    def run_strat(strat_json, live=False, simulate_orders=True):
        strat_dict = json.loads(strat_json)
        strat = Strategy()
        strat.load_from_dict(strat_dict)
        strat.run(viz=False, live=live, simulate_orders=simulate_orders)

        # serialize results for job result
        result_df = strat.quant_results
        return result_df.to_json()

    with Connection(CONN):
        worker = Worker(map(Queue, QUEUE_NAMES))
        worker.work()

def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)


def run_strat(strat_json, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy()
    strat.load_from_dict(strat_dict)
    strat.run(viz=False, live=live, simulate_orders=simulate_orders)

    # serialize results for job result
    result_df = strat.quant_results
    return result_df.to_json()


def queue_strat(strat_json, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy()
    strat.load_from_dict(strat_dict)

    if live and simulate_orders:
        q = get_queue('live')
        start_worker()

    elif live:
        q = get_queue('paper')
        start_worker()

    else:
        q = get_queue('backtest')


    job = q.enqueue(run_strat, job_id=strat.name, kwargs={'strat_json': strat_json, 'live': live, 'simulate_orders': simulate_orders})

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

if __name__ == '__main__':
    start_worker()
