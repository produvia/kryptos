import os
import time
from pathlib import Path
from google.api_core.exceptions import NotFound

from kryptos.settings import CONFIG_ENV, PERF_DIR, DEFAULT_CONFIG as CONFIG
from kryptos.utils import storage_client


def in_docker():
    if not os.path.exists("/proc/self/cgroup"):
        return False
    with open("/proc/self/cgroup", "r") as procfile:
        for line in procfile:
            fields = line.strip().split("/")
            if "docker" in fields:
                print("**Inside Docker container, will disable visualization**")
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
    file_specs = "{}_{}_{}".format(
        CONFIG["ASSET"], CONFIG["EXCHANGE"], CONFIG["DATA_FREQ"]
    )
    return os.path.join(algo_dir, file_specs)


def get_output_file_str(str, config):
    """Get output file from a string"""
    # perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(PERF_DIR, str)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = "{}_{}_{}".format(
        CONFIG["ASSET"], CONFIG["EXCHANGE"], CONFIG["DATA_FREQ"])
    return os.path.join(algo_dir, file_specs)


# def get_algo_dir(namespace):
#     algo_dir = os.path.join(os.path.abspath(PERF_DIR), namespace)
#     if not os.path.exists(algo_dir):
#         os.makedirs(algo_dir)
#     return algo_dir


def get_algo_dir(strat):
    """Modifed version of catalyst get_algo_folder"""
    home_dir = str(Path.home())
    algo_folder = os.path.join(home_dir, ".catalyst/data/live_algos", strat.id)
    os.makedirs(algo_folder, exist_ok=True)
    return algo_folder


def get_stats_dir(strat):
    mode_dir = f"stats_{strat.mode}"
    algo_folder = get_algo_dir(strat)
    stats_folder = os.path.join(algo_folder, mode_dir)
    return stats_folder


def get_algo_state_file(strat):
    mode_state_file = f"context.state_{strat.mode}.p"
    algo_folder = get_algo_dir(strat)
    return os.path.join(algo_folder, mode_state_file)


def get_stats_bucket():

    if CONFIG_ENV == "dev":
        bucket_name = "dev_strat_stats"
    else:
        bucket_name = "strat_stats"

    try:
        stats_bucket = storage_client.get_bucket(bucket_name)
    except NotFound:
        stats_bucket = storage_client.create_bucket(bucket_name)

    return stats_bucket


def save_analysis_to_storage(strat, results):

    strat.log.debug("Saving final performance to disk")
    folder = get_stats_dir(strat)
    filename = os.path.join(folder, "final_performance.csv")

    os.makedirs(folder, exist_ok=True)
    with open(filename, "w") as f:
        results.to_csv(f)

    strat.log.debug("Uploading final performance to storage")

    stats_bucket = get_stats_bucket()

    blob_name = f"{strat.id}/stats_{strat.mode}/final_performance.csv"
    blob = stats_bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    url = "https://storage.cloud.google.com/strat_stats/{blob_name}"
    strat.log.info(f"Uploaded strat performance")
    strat.log.info(f"Performance URL: {url}")
    return url


def save_plot_to_storage(strat, plot_file):
    strat.log.debug("Uploading summary plot to storage")

    stats_bucket = get_stats_bucket()

    blob_name = f"{strat.id}/stats_{strat.mode}/summary_plot.png"
    blob = stats_bucket.blob(blob_name)
    blob.upload_from_filename(plot_file)
    url = "https://storage.cloud.google.com/strat_stats/{blob_name}"
    strat.log.info(f"Uploaded strat plot to storage")
    strat.log.info(f"Plot URL: {url}")
    return url


def save_stats_to_storage(strat):
    # the following file was written to disk via catalyst
    # during it's repeated _save_stats_csv() method
    # after every handle_data

    # However this file won't be written until the end of the iteration,
    # so upload occurs the followign iteration
    strat.log.debug("Uploading previous iteration stats")
    stats_folder = get_stats_dir(strat)

    timestr = time.strftime("%Y%m%d")
    filename = os.path.join(stats_folder, "{}.csv".format(timestr))

    stats_bucket = get_stats_bucket()

    blob_name = f"{strat.id}/stats_{strat.mode}/{timestr}".format(timestr)
    blob = stats_bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    strat.log.info(f"Uploaded iteration {strat.state.i - 1} statistics")
    return blob_name, stats_bucket.name


def upload_state_to_storage(strat):
    stats_bucket = get_stats_bucket()
    filename = get_algo_state_file(strat)
    blob_name = f"{strat.id}/context.state_{strat.mode}.p"

    strat.log.debug(f"Uploading state from local catalyst file")

    blob = stats_bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    strat.log.info(f"Uploaded strat state to storage")
    return blob_name, stats_bucket.name


def load_state_from_storage(strat):
    strat.log.debug("Checking for previous stored state")
    stats_bucket = get_stats_bucket()
    filename = get_algo_state_file(strat)
    blob_name = f"{strat.id}/context.state_{strat.mode}.p"

    # ensure file is created
    open(filename, "a+").close()

    try:
        blob = stats_bucket.blob(blob_name)
        blob.download_to_filename(filename)
        strat.log.info(f"Downloaded previous strat state")
        return True
    except NotFound:
        strat.log.info("No previous state file found")
        # prevent catalyst loading empty pickle
        os.remove(filename)
        return False
