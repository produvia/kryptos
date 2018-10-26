import os
import time
from pathlib import Path
from catalyst.exchange.utils.exchange_utils import get_algo_folder
from google.api_core.exceptions import NotFound

from kryptos.settings import PERF_DIR, DEFAULT_CONFIG as CONFIG
from kryptos.utils import storage_client


def in_docker():
    if not os.path.exists('/proc/self/cgroup'):
        return False
    with open('/proc/self/cgroup', 'r') as procfile:
        for line in procfile:
            fields = line.strip().split('/')
            if 'docker' in fields:
                print('**Inside Docker container, will disable visualization**')
                return True

    return False


def dump_to_csv(filename, results, context=None):
    results.rename_axis("date").to_csv(filename + ".csv")
    results.rename_axis("date").to_pickle(filename + ".p")


def get_output_file(algo, config):
    """Get output file from algorithm name"""
    # perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(PERF_DIR, algo.NAMESPACE)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = "{}_{}_{}".format(CONFIG["ASSET"], CONFIG["EXCHANGE"], CONFIG["DATA_FREQ"])
    return os.path.join(algo_dir, file_specs)


def get_output_file_str(str, config):
    """Get output file from a string"""
    # perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(PERF_DIR, str)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = "{}_{}_{}".format(CONFIG["ASSET"], CONFIG["EXCHANGE"], CONFIG["DATA_FREQ"])
    return os.path.join(algo_dir, file_specs)


def get_algo_dir(namespace):
    algo_dir = os.path.join(os.path.abspath(PERF_DIR), namespace)
    if not os.path.exists(algo_dir):
        os.makedirs(algo_dir)
    return algo_dir

def save_stats_to_storage(strat):
    # the following file was written to disk via catalyst
    # during it's repeated _save_stats_csv() method
    # after every handle_data

    # However this file won't be written until the end of the iteration,
    # so upload occurs the followign iteration
    strat.log.info('Uploading previous iteration stats')
    stats_folder = get_stats_dir(strat)

    timestr = time.strftime('%Y%m%d')
    filename = os.path.join(stats_folder, '{}.csv'.format(timestr))

    try:
        auth_bucket = storage_client.get_bucket("strat_stats")
    except NotFound:
        auth_bucket = storage_client.create_bucket('strat_stats')

    blob_name = f"{strat.id}/stats_{strat.mode}/{timestr}.csv".format(timestr)
    blob = auth_bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    strat.log.info(f"Uploaded strat stats to {blob_name}")
    return blob_name, auth_bucket.name

