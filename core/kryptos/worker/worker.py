import os
import time
from threading import Thread
import signal
import sys

from logbook.compat import RedirectLoggingHandler
import logbook

from rq import Queue, get_failed_queue

from rq.worker import HerokuWorker as Worker
from rq.suspension import suspend
from rq.job import Job
from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry

from kryptos.logger import setup_logging, logger_group

client = Client(transport=HTTPTransport)

# Because the workers are running in separate processes,
# calling worker methods such handle_warm_shutdown_request() and request_stop_sigrtmin()
# cause the shutdown of the main process instead of an individual worker

# here we are setting a job to be killed via redis key,
# and then sending SIGINT from within the job process
# to allow for graceful shutdown and analyze() of strategy

# another solution would be setting a flag in the job's meta for the strategy to quit
# but this seems to not work correctly from outside the job
# https://github.com/rq/rq/issues/684

KILL_KEY = "rq:jobs:kill"


class StratJob(Job):
    def kill(self):
        """ Force kills the current job causing it to fail """
        if self.is_started:
            self.connection.sadd(KILL_KEY, self.get_id())

    def _execute(self):
        def check_kill(conn, id, interval=1):
            while True:
                res = conn.srem(KILL_KEY, id)
                if res > 0:
                    os.kill(os.getpid(), signal.SIGINT)
                time.sleep(interval)

        t = Thread(target=check_kill, args=(self.connection, self.get_id()))
        t.start()
        return super()._execute()


class StratQueue(Queue):
    job_class = StratJob


class StratWorker(Worker):
    imminent_shutdown_delay = 20
    queue_class = StratQueue
    job_class = StratJob

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        register_sentry(client, self)

        self.logger = logbook.Logger(f"WORKER:{os.getpid()}")
        logger_group.add_logger(self.logger)
        setup_logging()

    def shutdown_job(self):
        self.logger.warning("Suspending worker connection")
        suspend(self.connection)
        job = self.get_current_job()
        if job is None:
            self.logger.info("No current job, killing worker process")
            return os.kill(os.getpid(), signal.SIGRTMIN)

        self.logger.warning("Initiating job cleanup")
        self.logger.warning(f"Attempting requeue current job {job.id}")
        self.logger.warning("quarantining job")
        fq = get_failed_queue()
        fq.quarantine(job, exc_info="Graceful shutdown")

        self.logger.info("Setting job as PAUSED")
        job.meta["PAUSED"] = True
        job.save()
        self.logger.warning(f"Moving job {job.id} back to queue")
        fq.requeue(job.id)
        self.logger.warning("Gracefully requeued job")
        self.logger.warning("Sending SIGRTMIN to own process to kill self and job")
        # job.kill()  # causes algo to exit gracefully
        os.kill(os.getpid(), signal.SIGRTMIN)

    def request_stop_sigrtmin(self, signum, frame):
        self.logger.warning("Received SIGRTMIN request stop")
        if self.imminent_shutdown_delay == 0:
            self.logger.warning("Imminent shutdown, raising ShutDownImminentException immediately")
            self.request_force_stop_sigrtmin(signum, frame)
        else:
            self.logger.warning(
                "Imminent shutdown, raising ShutDownImminentException in %d seconds",
                self.imminent_shutdown_delay,
            )
            signal.signal(signal.SIGRTMIN, self.request_force_stop_sigrtmin)
            signal.signal(signal.SIGALRM, self.request_force_stop_sigrtmin)
            signal.alarm(self.imminent_shutdown_delay)
            self.shutdown_job()
