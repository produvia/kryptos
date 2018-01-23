import os
from logbook import Logger
from catalyst.exchange.exchange_bundle import ExchangeBundle

from crypto_platform import algos


ALGOS = os.path.dirname(os.path.abspath(algos.__file__))


log = Logger('Load')


def import_with_3(module_name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_with_2(module_name, path):
    import imp
    return imp.load_source(module_name, path)


def get_algo(filename):
    """Imports a module from filename as a string"""
    log.info('Attempting to import {}'.format(filename))
    module_name = os.path.splitext(filename)[0]

    try:
        algo_module = import_with_3(
            module_name, os.path.join(ALGOS, filename))

    except ImportError:
        algo_module = import_with_2(
            module_name, os.path.join(ALGOS, filename))

    except Exception as e:
        log.warn('Could not import algo {} by namespace'.format(module_name))
        log.error(e)
        return

    return algo_module


def load_by_name(namespace):
    algo = None
    f = namespace + '.py'
    algo = get_algo(f)

    if hasattr(algo, 'NAMESPACE'):
        return algo

    log.info('Searching algo files for {} namespace'.format(namespace))
    for a in load_algos():
        if a.NAMESPACE == namespace:
            return a


def load_algos():
    algos = []
    log.info('Grabbing algos from {}'.format(ALGOS))
    for f in os.listdir(ALGOS):
        if '__' not in f and f[-3:] == '.py':
            algo = get_algo(f)
            if hasattr(algo, 'NAMESPACE'):
                algos.append(algo)
    return algos


def ingest_exchange(config):
    """
    Ingest data for the given exchange.
    """

    if config.BUY_EXCHANGE is None:
        log.error("must specify an exchange name")

    exchange_bundle = ExchangeBundle(config.BUY_EXCHANGE)

    log.info('Ingesting exchange bundle {}...'.format(config.BUY_EXCHANGE))
    exchange_bundle.ingest(
        data_frequency=config.DATA_FREQUENCY,
        include_symbols=config.ASSET,
        exclude_symbols=None,
        start=config.START,
        end=config.END,
        show_progress=True,
        show_breakdown=False,
        show_report=False,
        csv=None
    )
