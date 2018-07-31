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


REDIS_HOST = os.getenv('REDIS_HOST', '10.0.0.3')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

CONN = redis.Redis(host='35.233.161.198', port=REDIS_PORT)

log = logbook.Logger('WorkerManager')
logger_group.add_logger(log)

def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)


def run_strat(strat_json, strat_id, live=False, simulate_orders=True):
    strat_dict = json.loads(strat_json)
    strat = Strategy.from_dict(strat_dict)
    strat.id = strat_id

    strat.run(viz=False, live=live, simulate_orders=simulate_orders, as_job=True)
    result_df = strat.quant_results

    return result_df.to_json()


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

        log.info('Starting worker for BACKTEST queue')
        multiprocessing.Process(target=Worker(['backtest'],).work).start()

        log.info('Starting worker for PAPER/LIVE queues')
        multiprocessing.Process(target=Worker(['paper', 'live']).work).start()



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



# def retry_handler(job, exc_type, exc_value, traceback):
#     job.meta.setdefault('failures', 0)
#     job.meta['failures'] += 1
#
#     # Too many failures
#     if job.meta['failures'] >= MAX_FAILURES:
#         log.warn('job %s: failed too many times times - moving to failed queue' % job.id)
#         job.save()
#         return True
#
#     # Requeue job and stop it from being moved into the failed queue
#     log.warn('job %s: failed %d times - retrying' % (job.id, job.meta['failures']))
#
#     fq = get_failed_queue()
#     fq.quarantine(job, Exception('Some fake error'))
#     # assert fq.count == 1
#
#     job.meta['failures'] += 1
#     job.save()
#     fq.requeue(job.id)
#
#     # for q_name in QUEUE_NAMES:
#     #     q = get_queue(q_name)
#     #     if q.name == job.origin:
#     #         q.enqueue_job(job)
#     #         return False
#
#     # Can't find queue, which should basically never happen as we only work jobs that match the given queue names and
#     # queues are transient in rq.
#     # log.warn('job %s: cannot find queue %s - moving to failed queue' % (job.id, job.origin))
#     # return True
#
# def spawn_worker_process(queues, name=None, burst=False, allow_retry=True):
#     worker = Worker(QUEUE_NAMES, name=name)
#     if allow_retry:
#         worker.push_exc_handler(retry_handler)
#     multiprocessing.Process(target=worker.work, kwargs={'burst': True}).start()




if __name__ == '__main__':
    manage_workers()
