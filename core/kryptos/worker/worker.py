import os
import sys
import time
from threading import Thread
import signal

from logbook.compat import RedirectLoggingHandler, redirect_logging


from rq import Queue, Worker, get_failed_queue

# from rq.worker import HerokuWorker as Worker
from rq.suspension import suspend
from rq.job import Job
from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry

from kryptos.logger import logger_group, setup_logging

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
        self.log.addHandler(RedirectLoggingHandler())
        setup_logging()


    # def shutdown_job(self):
    #     self.log.warning("Suspending worker connection")
    #     suspend(self.connection)
    #     self.log.warning("Initiating job cleanup")
    #     job = self.get_current_job()

    #     self.log.warning("quarantining job")
    #     fq = get_failed_queue()
    #     fq.quarantine(job, exc_info="Instance Shutdown")

    #     self.log.warning("Setting job as PAUSED")
    #     job.meta["PAUSED"] = True
    #     job.save()
        # self.log.warning(f"Moving job {job.id} back to queue")
        # fq.requeue(job.id)
        # self.log.warning("Sending job kill signal to attempt analysis upload")
        # job.kill()  # causes algo to exit gracefully

    # def request_stop_sigrtmin(self, signum, frame):
    #     if self.imminent_shutdown_delay == 0:
    #         self.log.warning("Imminent shutdown, raising ShutDownImminentException immediately")
    #         self.request_force_stop_sigrtmin(signum, frame)
    #     else:
    #         self.shutdown_job()
    #         self.log.warning(
    #             "Imminent shutdown, raising ShutDownImminentException in %d seconds",
    #             self.imminent_shutdown_delay,
    #         )
    #         signal.signal(signal.SIGRTMIN, self.request_force_stop_sigrtmin)
    #         signal.signal(signal.SIGALRM, self.request_force_stop_sigrtmin)
    #         signal.alarm(self.imminent_shutdown_delay)
