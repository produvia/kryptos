import os
import redis
from rq import Worker, Queue, Connection

listen = ["high", "default", "low"]

conn = redis.Redis(host='redis', port=6379)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
