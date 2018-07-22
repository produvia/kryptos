import time
from logbook import Logger
import multiprocessing
from catalyst.exchange.exchange_bundle import ExchangeBundle
from rq import Connection, Worker

from kryptos import logger_group
from kryptos.worker.worker import CONN, get_queue


log = Logger("INGESTER")
logger_group.add_logger(log)


def ingest_exchange(exchange, symbol=None):
    exchange_bundle = ExchangeBundle(exchange)
    log.info(f'Ingesting {exchange} daily data')
    if symbol is None:
        log.warn(f'Queuing ingest {exchange} for all symbols')
    else:
        log.warn(f'Queuing ingest {exchange} for {symbol}')
    exchange_bundle.ingest(
        'daily',
        include_symbols=symbol,
        show_progress=True,
        show_breakdown=True,
        show_report=True
    )
    log.info(f'Done ingesting daily {exchange} data')
    log.info(f'Ingesting {exchange} minute data')
    exchange_bundle.ingest(
        'minute',
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

def queue_ingest(exchange, symbol=None):
    if symbol is None:
        log.warn(f'Queuing ingest {exchange} for all symbols')
    else:
        log.warn(f'Queuing ingest {exchange} for {symbol}')

    q = get_queue("ingest")
    q.enqueue(load.ingest_exchange, args=(exchange, symbol,))



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
