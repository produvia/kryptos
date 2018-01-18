import sys
import os
from os.path import basename


def dump_to_csv(filename, results, context=None):
    results.to_csv(filename)


def get_output_file(algo, config):
    # perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(config.PERF_DIR, algo.NAMESPACE)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = '{}_{}_{}'.format(config.ASSET, config.BUY_EXHANGE, config.DATA_FREQUENCY)
    return os.path.join(algo_dir, file_specs)
