import os
from logbook import Logger
from crypto_platform.algos import single_asset, multi_asset

# ALGOS = os.path.join(os.path.abspath('..'), 'algos')
# ALGOS = os.path.abspath(algos.__file__)
# SINGLE_ALGOS = os.path.join(ALGOS, 'single_asset')
# MULTI_ALGSOS = os.path.join(ALGOS, 'multi_asset')

SINGLE_ALGOS = os.path.dirname(os.path.abspath(single_asset.__file__))
MULTI_ALGSOS = os.path.dirname(os.path.abspath(multi_asset.__file__))


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
            module_name, os.path.join(SINGLE_ALGOS, filename))

    except ImportError:
        algo_module = import_with_2(
            module_name, os.path.join(SINGLE_ALGOS, filename))

    return algo_module



def load_algos(dir):
    algos = []
    log.info('Grabbing algos from {}'.format(dir))
    for f in os.listdir(dir):
        if '__' not in f:
            algo = get_algo(f)
            algos.append(algo)
            log.info('Loaded {}'.format(algo.NAMESPACE))
            yield algo

def single_asset_algos():
    return load_algos(SINGLE_ALGOS)

def multi_asset_algos():
    return load_algos(MULTI_ALGSOS)

