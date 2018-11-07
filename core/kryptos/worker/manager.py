import sys
import redis
from rq import Connection, get_failed_queue
import click
import time
import logbook
import signal
import multiprocessing

import datetime

from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry
from rq.suspension import is_suspended, resume
from rq.exceptions import ShutDownImminentException

from kryptos import logger_group, setup_logging

from kryptos.utils import tasks
from kryptos.settings import QUEUE_NAMES, REDIS_HOST, REDIS_PORT, SENTRY_DSN, CONFIG_ENV

from kryptos.worker.worker import StratQueue, StratWorker as Worker


client = Client(SENTRY_DSN, transport=HTTPTransport)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


log = logbook.Logger("MANAGER")
logger_group.add_logger(log)

WORKER_PROCESSES = []


def get_queue(queue_name):
    return StratQueue(queue_name, connection=CONN)


def workers_required(queue_name):
    q = get_queue(queue_name)
    return len(q)


def spawn_worker(q, burst=False):
    log.info(f"Creating {q} worker")

    worker = Worker([q], exception_handlers=[exc_handler])
    proc = multiprocessing.Process(target=worker.work, kwargs={"burst": burst})
    proc.daemon = True
    proc.start()

    WORKER_PROCESSES.append(proc)
    return proc


def remove_zombie_workers():
    log.warn("Removing zombie workers")
    workers = Worker.all(connection=CONN)
    for worker in workers:
        if len(worker.queues) < 1:
            log.warn("f")
            log.warn(f"{worker} is a zombie, killing...")
            job = worker.get_current_job()
            if job is not None:
                job.ended_at = datetime.datetime.utcnow()
                worker.failed_queue.quarantine(
                    job, exc_info=("Dead worker", "Moving job to failed queue")
                )
            worker.register_death()


# TODO remove old workers that weren't removed during SIGKILL
# these workers stay in redis memory and have a queue (not zombie) but no job
# but they have actually been killed, and won't restart
def remove_stale_workers():
    log.warn("Removing stale workers")
    workers = Worker.all(connection=CONN)
    for worker in workers:
        for q in ["paper", "live", "backtest"]:
            if q in worker.queue_names() and worker.get_current_job() is None:
                log.warn("Removing stale worker {}".format(worker))
                worker.clean_registries()
                worker.register_death()


def monitor_worker_shutdown(signum, frame):
    """Keeps main process alive until all worker processes shutdown"""
    log.warning("Caught SIGTERM, monitoring worker process shutdown")

    while len(WORKER_PROCESSES) > 0:
        for p in WORKER_PROCESSES:
            if p.is_alive():
                log.warning(f"waiting on process {p.pid} to terminate")
            else:
                log.info(f"Process {p.pid} has finished")
                WORKER_PROCESSES.remove(p)
        time.sleep(0.5)
    log.warning("Shutdown process complete, exiting")
    sys.exit(0)


@click.command()
def manage_workers():
    log.info(f"Starting core service in {CONFIG_ENV} env")
    log.info(f"Using Redis connection {REDIS_HOST}:{REDIS_PORT}")

    remove_zombie_workers()
    # remove_stale_workers()
    # start main worker
    with Connection(CONN):
        if is_suspended(CONN):
            log.warning("Resuming connection for startup")
            resume(CONN)

        requeue_terminated_fail_jobs()

        log.info("Starting initial workers")
        log.info("Starting worker for BACKTEST queue")
        spawn_worker("backtest")

        log.info("Starting worker for PAPER queues")
        spawn_worker("paper")

        log.info("Starting worker for LIVE queues")
        spawn_worker("live")

        log.info("Starting worker for TA queue")
        spawn_worker("ta")

        # create paper/live queues when needed
        while not is_suspended(CONN):
            for q in QUEUE_NAMES:
                required = workers_required(q)
                for i in range(required):
                    spawn_worker(q, burst=True)
                    time.sleep(5)

            time.sleep(2)
        else:
            log.warning("Instance is shutting down")


def requeue_terminated_fail_jobs():
    """Checks for failed jobs caused by work horse cold shutdown

    This serves as a final catch if jobs weren't re-queued on shutdown
    """

    fq = get_failed_queue()

    log.info("Checking for terminated jobs in failed queue")
    for job in fq.jobs:
        log.warning(job.exc_info)
        log.warning(f"Job {job.id} - exc_info: {job.exc_info}")
        if job.exc_info and "terminated unexpectedly" in job.exc_info:
            log.warning(f"Requeing terminated job: {job.id}")
            fq.requeue(job.id)


def exc_handler(job, exc_type, exc_value, traceback):

    from ccxt.base.errors import AuthenticationError
    from catalyst.exchange.exchange_errors import ExchangeRequestError

    auth_errors = [AuthenticationError, ExchangeRequestError]

    if exc_type in auth_errors:
        if job.meta.get("telegram_id"):
            tasks.queue_notification(f"Auth error: {exc_value}", job.meta["telegram_id"])

        else:
            log.warning("No Telegram, could not notify")

        log.critical(exc_value)
        job.save()

        return True

    if exc_type == SystemExit:
        log.notice("Strat was set killed, not requeuing or retrying")
        job.save()
        job.cleanup()
        return False

    if exc_type == ShutDownImminentException:
        log.warning("Job has been stopped to instance shutdown")
        return True

    if job.meta.get("telegram_id"):
        tasks.queue_notification(f"Strategy has failed", job.meta["telegram_id"])

    else:
        log.warning("No Telegram, could not notify")

    log.error(f"Job raised {exc_type}")

    log.warn("job %s: moving to failed queue" % job.id)
    job.save()

    return True


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, monitor_worker_shutdown)
    setup_logging()
    manage_workers()
