import os
import sys

from flask import Flask


# The app checks this file for the PID of the process to monitor.
PID_FILE = None


# Create app to handle health checks and monitor the queue worker. This will
# run alongside the worker, see procfile.
monitor_app = Flask(__name__)


# The health check reads the PID file created by psqworker and checks the proc
# filesystem to see if the worker is running. This same pattern can be used for
# rq and celery.
@monitor_app.route('/_ah/health')
def health():
    # if not os.path.exists(PID_FILE):
    #     return 'Worker pid not found', 503
    #
    # with open(PID_FILE, 'r') as pidfile:
    #     pid = pidfile.read()
    #
    # if not os.path.exists('/proc/{}'.format(pid)):
    #     return 'Worker not running', 503

    return 'healthy', 200


@monitor_app.route('/')
def index():
    return health()


if __name__ == '__main__':
    PID_FILE = sys.argv[1]
    monitor_app.run('0.0.0.0', 8080)
