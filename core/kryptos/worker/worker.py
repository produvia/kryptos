import os
import time
from threading import Thread
import signal

from rq import Queue
from rq.worker import HerokuWorker as Worker
from rq.job import Job

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
    queue_class = StratQueue
    job_class = StratJob
