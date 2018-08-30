import os
import json
import redis
from rq import Queue, Connection, get_failed_queue
from rq.worker import HerokuWorker as Worker
from rq.handlers import move_to_failed_queue
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
from kryptos.settings import QUEUE_NAMES, get_from_datastore


SENTRY_DSN =  os.getenv('SENTRY_DSN', None)
client = Client(SENTRY_DSN, transport=HTTPTransport)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis-19779.c1.us-central1-2.gce.cloud.redislabs.com')
REDIS_PORT = os.getenv('REDIS_PORT', 19779)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) or get_from_datastore('REDIS_PASSWORD', 'production')

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


def remove_zombie_workers():
    log.warn('Removing zombie workers')
    workers = Worker.all(connection=CONN)
    for worker in workers:
        if len(worker.queues) < 1:
            log.warn("f")
            log.warn(f"{worker} is a zombie, killing...")
            job = worker.get_current_job()
            if job is not None:
                job.ended_at = datetime.datetime.utcnow()
                worker.failed_queue.quarantine(job, exc_info=("Dead worker", "Moving job to failed queue"))
            worker.register_death()

#TODO remove old workers that weren't removed during SIGKILL
# these workers stay in redis memory and have a queue (not zombie) but no job
# but they have actually been killed, and won't restart
def remove_stale_workers():
    log.warn('Removing stale workers')
    workers = Worker.all(connection=CONN)
    for worker in workers:
        for q in ['paper', 'live', 'backtest']:
            if q in worker.queue_names() and worker.get_current_job() is None:
                log.warn('Removing stale worker {}'.format(worker))
                worker.clean_registries()
                worker.register_death()



@click.command()
def manage_workers():
    # import before starting worker to loading during worker process
    # from kryptos.strategy import Strategy
    # from app.extensions import jsonrpc
    # from kryptos.utils.outputs import in_docker

    remove_zombie_workers()
    # remove_stale_workers()
    #start main worker
    with Connection(CONN):
        log.info('Starting initial workers')

        log.info('Starting worker for BACKTEST queue')
        backtest_worker = Worker(['backtest'])
        register_sentry(client, backtest_worker)
        multiprocessing.Process(target=backtest_worker.work).start()

        log.info('Starting worker for PAPER queues')
        paper_worker = Worker(['paper'], exception_handlers=[retry_handler, move_to_failed_queue])
        register_sentry(client, paper_worker)
        multiprocessing.Process(target=paper_worker.work).start()

        log.info('Starting worker for LIVE queues')
        live_worker = Worker(['live'], exception_handlers=[retry_handler, move_to_failed_queue])
        register_sentry(client, live_worker)
        multiprocessing.Process(target=live_worker.work).start()

        # create paper/live queues when needed
        while True:
            for q in QUEUE_NAMES:
                required = workers_required(q)
                for i in range(required):
                    log.info(f"Creating {q} worker")
                    worker = Worker([q], exception_handlers=[retry_handler, move_to_failed_queue])
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
    fq.quarantine(job, Exception(exc_value))
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
