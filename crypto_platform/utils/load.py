import os
from logbook import Logger
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

    except AttributeError:
        log.info('Skipping import of {}'.format(module_name))
        return

    return algo_module


def load_algos():
    algos = []
    log.info('Grabbing algos from {}'.format(ALGOS))
    for f in os.listdir(ALGOS):
        if '__' not in f and f[-3:] == '.py':
            algo = get_algo(f)
            algos.append(algo)
            log.info('Loaded {}'.format(algo.NAMESPACE))
            algos.append(algo)
    return algos
