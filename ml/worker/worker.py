import os
import redis
from rq import Connection, Worker
import logbook

from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry


SENTRY_DSN =  os.getenv('SENTRY_DSN', None)
client = Client(SENTRY_DSN, transport=HTTPTransport)

REDIS_HOST = os.getenv('REDIS_HOST', '10.138.0.4')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


log = logbook.Logger('MLWorker')

# log.warn(f'Using Redis connection {REDIS_HOST}:{REDIS_PORT}')


def start_worker():
    with Connection(CONN):
        worker = Worker(['ml'])
        register_sentry(client, worker)
        worker.work()



if __name__ == '__main__':
    start_worker()
