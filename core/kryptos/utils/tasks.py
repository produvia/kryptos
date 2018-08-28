import os
from rq import Connection, Queue
import redis


REDIS_HOST = os.getenv('REDIS_HOST', '10.138.0.4')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


def queue_notification(msg, telegram_id):
    with Connection(CONN):
        q = Queue('updates')
        q.enqueue(
            'updater.send_notification',
            msg=msg,
            telegram_id=telegram_id
        )

def enqueue_ml_calculate(df_current, name, idx, current_datetime, df_final, **kw):
    df_current_dict = df_current.to_dict()
    df_final_dict = df_final.to_dict()
    with Connection(CONN):
        q = Queue('ml')
        return q.enqueue(
            'worker.calculate',
            args=[df_current_dict, name, idx, current_datetime, df_final_dict],
            kwargs=kw
        )

def enqueue_ml_analyze(namespace, name, df_final, data_freq, extra_results):
    df_final_dict = df_final.to_dict()
    with Connection(CONN):
        q = Queue('ml')
        return q.enqueue(
            'worker.analyze',
            args=[namespace, name, df_final_dict, data_freq, extra_results]
        )
