import os
from kryptos.settings import PERF_DIR, DEFAULT_CONFIG as CONFIG

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
