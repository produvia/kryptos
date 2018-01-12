""" This script simply runs each algorithim within algos/single_asset/
The recorded results are saved to a csv file  and as a pickled pandas Dataframe
in scripts/performance_results
"""


import os
import tempfile
from catalyst import run_algorithm

from logbook import Logger
from crypto_platform.utils import load, outputs
from config import CONFIG

log = Logger('Strategy Runner')


def get_output_file(algo):
    perf_dir = CONFIG.PERF_DIR
    algo_dir = os.path.join(perf_dir, algo.NAMESPACE)
    os.makedirs(algo_dir, exist_ok=True)
    file_specs = '{}_{}_{}'.format(CONFIG.ASSETS[0], CONFIG.BUY_EXHANGE, CONFIG.DATA_FREQUENCY)
    return os.path.join(algo_dir, file_specs)


def run():
    for algo in load.single_asset_algos():
        log.info('Running {}'.format(algo.NAMESPACE))
        algo.CONFIG = CONFIG

        def analyze(context, results):
            output_file = get_output_file(algo)+ '.csv'
            log.info('Dumping result csv to {}'.format(output_file))
            outputs.dump_to_csv(output_file, results)

        run_algorithm(
            capital_base=CONFIG.CAPITAL_BASE,
            data_frequency=CONFIG.DATA_FREQUENCY,
            initialize=algo.initialize,
            handle_data=algo.handle_data,
            analyze=analyze,
            exchange_name=CONFIG.BUY_EXHANGE,
            algo_namespace=algo.NAMESPACE,
            base_currency=CONFIG.BASE_CURRENCY,
            start=CONFIG.START,
            end=CONFIG.END,
            output=get_output_file(algo) + '.p'
        )
        log.info('Run completed for {}'.format(algo.NAMESPACE))

if __name__ == '__main__':
    run()
