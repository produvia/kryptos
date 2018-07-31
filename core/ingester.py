import os
import time
from logbook import Logger
import multiprocessing
from catalyst.exchange.exchange_bundle import ExchangeBundle
from rq import Connection, Worker
import pandas as pd
import redis

from kryptos import logger_group

REDIS_HOST = os.getenv('REDIS_HOST', '10.0.0.3')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


log = Logger("INGESTER")
logger_group.add_logger(log)

def get_queue(queue_name):
    if queue_name in ['paper', 'live']:
        return Queue(queue_name, connection=CONN)
    return Queue(queue_name, connection=CONN)



def ingest_exchange(exchange, symbol=None, start=None, end=None):
    exchange_bundle = ExchangeBundle(exchange)
    if symbol is None:
        log.warn(f'Queuing ingest {exchange} for all symbols')
    else:
        log.warn(f'Queuing ingest {exchange} for {symbol}')

    log.warn(f'Will ingest timeframe {start} - {end}')

    log.info(f'Ingesting {exchange} daily data')
    exchange_bundle.ingest(
        'daily',
        start=pd.to_datetime(start, utc=True),
        end=pd.to_datetime(end, utc=True),
        include_symbols=symbol,
        show_progress=True,
        show_breakdown=True,
        show_report=True
    )
    log.info(f'Done ingesting daily {exchange} data')

    log.info(f'Ingesting {exchange} minute data')
    exchange_bundle.ingest(
        'minute',
        start=pd.to_datetime(start, utc=True),
        end=pd.to_datetime(end, utc=True),
        include_symbols=symbol,
        show_progress=True,
        show_breakdown=True,
        show_report=True
    )
    log.info(f'Done ingesting minute {exchange} data')
    log.info('Ingest completed')



def ingest_from_trade_config(config):
    """
    Ingest exchange bundle data for a given strategy time frame
    """

    if config.get("EXCHANGE") is None:
        log.error("must specify an exchange name")

    exchange_bundle = ExchangeBundle(config["EXCHANGE"])

    log.notice(
        "Ingesting {} exchange bundle {} - {}...".format(
            config["EXCHANGE"], config["START"], config["END"]
        )
    )
    exchange_bundle.ingest(
        data_frequency=config["DATA_FREQ"],
        include_symbols=config["ASSET"],
        exclude_symbols=None,
        start=pd.to_datetime(config["START"], utc=True),
        end=pd.to_datetime(config["END"], utc=True),
        show_progress=True,
        show_breakdown=True,
        show_report=True,
        csv=None,
    )

def queue_ingest(exchange, symbol=None, start=None, end=None):
    if symbol is None:
        log.warn(f'Queuing ingest {exchange} for all symbols')
    else:
        log.warn(f'Queuing ingest {exchange} for {symbol}')

    q = get_queue("ingest")
    return q.enqueue(load.ingest_exchange, args=(exchange, symbol, start, end))



if __name__ == '__main__':

    with Connection(CONN):
        log.info('Starting ingest worker')
        multiprocessing.Process(target=Worker(['ingest']).work).start()

    # allow worker to start up
    time.sleep(5)

    while True:
        for ex in ['bitfinex', 'bittrex', 'poloniex']:
            ingest_exchange(ex)

        # re-ingest every 12 hours
        time.sleep(43200)
