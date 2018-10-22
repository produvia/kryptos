import os
import json
import redis
from rq import Connection
from rq.worker import HerokuWorker as Worker
import logbook

from telegram import Bot

from app.settings import get_from_datastore

log = logbook.Logger("UPDATER")

CONFIG_ENV = os.getenv("CONFIG_ENV")

if CONFIG_ENV == "dev":
    log.warn("Using dev telegram token")
    TELEGRAM_TOKEN = get_from_datastore("TELEGRAM_TOKEN", "dev")
else:
    log.warn("Using production telegram token")
    TELEGRAM_TOKEN = get_from_datastore("TELEGRAM_TOKEN", "production")


bot = Bot(TELEGRAM_TOKEN)

REDIS_HOST = os.getenv("REDIS_HOST", "10.0.0.3")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


def send_notification(msg, telegram_id):
    bot.send_message(text=msg, chat_id=telegram_id)


def start_worker():
    with Connection(CONN):
        log.info("Starting update worker")
        worker = Worker("updates")
        worker.work()


if __name__ == "__main__":
    start_worker()
