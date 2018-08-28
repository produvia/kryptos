import os
import json
import redis
from rq import Queue, Connection, Worker, get_failed_queue
import click
import multiprocessing
import time
import logbook
from catalyst.exchange.exchange_bundle import ExchangeBundle

from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry

from kryptos import logger_group
from kryptos.strategy import Strategy
from kryptos.utils.outputs import in_docker
from kryptos.utils import tasks
from kryptos.settings import QUEUE_NAMES


SENTRY_DSN =  os.getenv('SENTRY_DSN', None)
client = Client(SENTRY_DSN, transport=HTTPTransport)

REDIS_HOST = os.getenv('REDIS_HOST', '10.138.0.4')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


log = logbook.Logger('WorkerManager')
logger_group.add_logger(log)
log.warn(f'Using Redis connection {REDIS_HOST}:{REDIS_PORT}')

def get_queue(queue_name):
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
        backtest_worker = Worker(['backtest'])
        register_sentry(client, backtest_worker)
        multiprocessing.Process(target=backtest_worker.work).start()

        log.info('Starting worker for PAPER queues')
        paper_worker = Worker(['paper'], exception_handlers=[retry_handler])
        register_sentry(client, paper_worker)
        multiprocessing.Process(target=paper_worker.work).start()

        log.info('Starting worker for LIVE queues')
        live_worker = Worker(['live'], exception_handlers=[retry_handler])
        register_sentry(client, live_worker)
        multiprocessing.Process(target=live_worker.work).start()

        # create paper/live queues when needed
        while True:
            for q in QUEUE_NAMES:
                required = workers_required(q)
                log.debug(f"{required} workers required for {q}")
                for i in range(required):
                    log.info(f"Creating {q} worker")
                    worker = Worker([q], exception_handlers=[retry_handler])
                    register_sentry(client, live_worker)
                    multiprocessing.Process(target=worker.work, kwargs={'burst': True}).start()


            time.sleep(5)




def retry_handler(job, exc_type, exc_value, traceback):
    MAX_FAILURES = 3
    job.meta.setdefault('failures', 0)
    job.meta['failures'] += 1

    # Too many failures
    if job.meta['failures'] >= MAX_FAILURES:
        log.warn('job %s: failed too many times times - moving to failed queue' % job.id)
        job.save()
        tasks.queue_notification(f'Strategy has failed', job.meta['telegram_id'])
        return True

    # Requeue job and stop it from being moved into the failed queue
    log.warn('job %s: failed %d times - retrying' % (job.id, job.meta['failures']))

    fq = get_failed_queue()
    fq.quarantine(job, Exception('Some fake error'))
    # assert fq.count == 1

    job.meta['failures'] += 1
    job.save()
    fq.requeue(job.id)

    # Can't find queue, which should basically never happen as we only work jobs that match the given queue names and
    # queues are transient in rq.
    log.warn('job %s: cannot find queue %s - moving to failed queue' % (job.id, job.origin))
    return True


if __name__ == '__main__':
    manage_workers()