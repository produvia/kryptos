import os
import pandas as pd
from logbook import Logger

from kryptos import strategies, logger_group


STRATS = os.path.dirname(os.path.abspath(strategies.__file__))

log = Logger("Load")


def import_with_3(module_name, path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_with_2(module_name, path):
    import imp

    return imp.load_source(module_name, path)


def get_strat(path):
    """Imports a module from filename as a string"""
    log.info("Attempting to import {}".format(path))
    filename = os.path.split(path)[1]
    module_name = os.path.splitext(filename)[0]

    try:
        strat_module = import_with_3(module_name, os.path.join(STRATS, filename))

    except ImportError:
        strat_module = import_with_2(module_name, os.path.join(STRATS, filename))

    except Exception as e:
        log.warn("Could not import strat {} by name".format(module_name))
        log.error(e)
        raise e

    try:
        return getattr(strat_module, 'strat')

    except AttributeError:
        log.warn("No Strategy object found in {}. Note that the object must be named `strat`".format(module_name))
        log.error(e)
        raise e



    return strat_module


def load_by_name(namespace):
    strat = None
    f = namespace + ".py"
    strat = get_strat(f)

    if hasattr(strat, "NAMESPACE"):
        return strat

    log.info("Searching strat files for {} namespace".format(namespace))
    for s in load_strats():
        log.warning(getattr(s, "NAMESPACE", None))
        if s.NAMESPACE == namespace:
            strat = s

    if strat is None:
        raise FileNotFoundError("Could not import strategy with namespace: {}".format(namespace))


def load_strats():
    strats = []
    log.info("Grabbing strats from {}".format(STRATS))
    for f in os.listdir(STRATS):
        if "__" not in f and f[-3:] == ".py":
            strat = get_strat(f)
            if hasattr(strat, "NAMESPACE"):
                strats.append(strat)
    return strats
