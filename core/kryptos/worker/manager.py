import os
import redis
from rq import Connection, get_failed_queue
import click
import multiprocessing
import time
import logbook
import signal

import datetime

from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry

from kryptos import logger_group

from kryptos.utils import tasks
from kryptos.settings import QUEUE_NAMES, REDIS_HOST, REDIS_PORT, SENTRY_DSN, CONFIG_ENV

from kryptos.worker.worker import StratQueue, StratWorker as Worker


client = Client(SENTRY_DSN, transport=HTTPTransport)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


log = logbook.Logger("WorkerManager")
logger_group.add_logger(log)
log.warn(f"Using Redis connection {REDIS_HOST}:{REDIS_PORT}")


def get_queue(queue_name):
    return StratQueue(queue_name, connection=CONN)


def workers_required(queue_name):
    q = get_queue(queue_name)
    return len(q)


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


def kill_marked_jobs():
    workers = Worker.all()
    log.debug(f"Checking {len(workers)} workers for jobs marked to kill")
    for w in workers:
        if w.get_current_job():
            log.debug(f"Checking {w.name} job")
            meta = w.get_current_job().meta
            if meta.get("MARK_KILL"):
                log.warning(f"Killing job by sending kill signal to worker pid {w.pid}")
                # ok.kill_horse()
                # os.kill(w.pid, signal.SIGTERM)
                # raise Exception('Shutting down worker marked to kill job')
                # w.handle_warm_shutdown_request()

                # w.request_stop_sigrtmin()
                # raise ShutDownImminentException


def shutdown_workers(signum, frame):
    log.warning("Sending SIGTERM to each worker to start graceful shutdown")
    for w in Worker.all():
        log.warning(f"Killing worker {w.pid}")
        # w.handle_warm_shutdown_request()
        os.kill(w.pid, signal.SIGTERM)
        signal.pause()
        w.get_current_job().kill()


@click.command()
def manage_workers():
    log.info(f"Starting core service in {CONFIG_ENV} env")

    remove_zombie_workers()
    # remove_stale_workers()
    # start main worker
    with Connection(CONN):
        # signal.signal(signal.SIGTERM, shutdown_workers)

        log.info("Starting initial workers")
        log.info("Starting worker for BACKTEST queue")
        backtest_worker = Worker(["backtest"])
        register_sentry(client, backtest_worker)
        multiprocessing.Process(target=backtest_worker.work).start()

        log.info("Starting worker for PAPER queues")
        paper_worker = Worker(["paper"], exception_handlers=[retry_handler])
        register_sentry(client, paper_worker)
        multiprocessing.Process(target=paper_worker.work).start()

        log.info("Starting worker for LIVE queues")
        live_worker = Worker(["live"], exception_handlers=[retry_handler])
        register_sentry(client, live_worker)
        multiprocessing.Process(target=live_worker.work).start()

        log.info("Starting worker for TA queue")
        ta_worker = Worker(["ta"])
        register_sentry(client, ta_worker)
        multiprocessing.Process(target=ta_worker.work).start()

        # create paper/live queues when needed
        while True:
            for q in QUEUE_NAMES:
                required = workers_required(q)
                for i in range(required):
                    log.info(f"Creating {q} worker")
                    worker = Worker([q], exception_handlers=[retry_handler])
                    register_sentry(client, worker)
                    multiprocessing.Process(target=worker.work, kwargs={"burst": True}).start()

            time.sleep(5)


def retry_handler(job, exc_type, exc_value, traceback):
    MAX_FAILURES = 3
    job.meta.setdefault("failures", 0)
    job.meta["failures"] += 1

    log.error(f"Job raised {exc_type}")

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

    # Too many failures
    if job.meta["failures"] >= MAX_FAILURES:
        if job.meta.get("telegram_id"):
            tasks.queue_notification(f"Strategy has failed", job.meta["telegram_id"])

        else:
            log.warning("No Telegram, could not notify")

        log.warn("job %s: failed too many times times - moving to failed queue" % job.id)
        job.save()

        return True

    # Requeue job and stop it from being moved into the failed queue
    log.warn("job %s: failed %d times - retrying" % (job.id, job.meta["failures"]))

    fq = get_failed_queue()
    fq.quarantine(job, exc_type(exc_value))
    # assert fq.count == 1

    job.meta["failures"] += 1
    job.save()
    fq.requeue(job.id)

    # Can't find queue, which should basically never happen as we only work jobs that match the given queue names and
    # queues are transient in rq.
    log.warn("job %s: cannot find queue %s - moving to failed queue" % (job.id, job.origin))
    return True


if __name__ == "__main__":
    manage_workers()
