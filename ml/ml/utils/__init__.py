import os

from ml.settings import PERF_DIR


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


# TODO set up perf dir to be available to alls services
def get_algo_dir(namespace):
    algo_dir = os.path.join(os.path.abspath(PERF_DIR), namespace)
    if not os.path.exists(algo_dir):
        os.makedirs(algo_dir)
    return algo_dir
