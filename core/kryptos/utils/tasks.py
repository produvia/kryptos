from rq import Connection, Queue
import redis
from kryptos.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, DEFAULT_CONFIG

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)


def queue_notification(msg, telegram_id):
    if telegram_id is None:
        return
    with Connection(CONN):
        q = Queue('updates')
        q.enqueue(
            'updater.send_notification',
            msg=msg,
            telegram_id=telegram_id
        )


def enqueue_ml_calculate(df_current, namespace, name, idx, current_datetime, hyper_params, df_final, **kw):
    df_current_json = df_current.to_json()
    df_final_json = df_final.to_json()
    with Connection(CONN):
        q = Queue('ml')
        return q.enqueue(
            'worker.calculate',
            args=[namespace, df_current_json, name, idx, current_datetime, df_final_json, DEFAULT_CONFIG['DATA_FREQ'], DEFAULT_CONFIG['MINUTE_FREQ'], hyper_params],
            kwargs=kw,
            timeout=str(DEFAULT_CONFIG['MINUTE_FREQ']) + 'm'  # allow job to run for full iteration
        )


def enqueue_ml_analyze(namespace, name, df_final, df_results, data_freq, extra_results):
    df_final_json = df_final.to_json()
    df_results_json = df_results.to_json()
    with Connection(CONN):
        q = Queue('ml')
        return q.enqueue(
            'worker.analyze',
            args=[namespace, name, df_final_json, df_results_json, data_freq, extra_results],
            timeout=str(DEFAULT_CONFIG['MINUTE_FREQ']) + 'm'  # allow job to run for full iteration
        )
