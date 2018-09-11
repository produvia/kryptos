import os
from google.cloud import datastore

PLATFORM_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.dirname(PLATFORM_DIR)
PERF_DIR = os.path.join(BASE_DIR, "performance_results")
LOG_DIR = os.path.join(BASE_DIR, "logs")

STRAT_DIR = os.path.join(PLATFORM_DIR, "strategy")
DEFAULT_CONFIG_FILE = os.path.join(STRAT_DIR, "config.json")

def get_from_datastore(config_key, env):
    ds = datastore.Client()
    product_key = ds.key('Settings', env)
    entity = ds.get(product_key)

    return entity[config_key]

## Machine Learning Settings

class MLConfig(object):

    DEBUG = True

    ## MACHINE LEARNING GENERAL SETTINGS
    """
        1 - Regression
        2 - Binary Classification (DOWN / UP)
        3 - Multiclass Classification (DOWN / KEEP / UP)
    """
    CLASSIFICATION_TYPE = 1

    if CLASSIFICATION_TYPE == 2:
        THRESHOLD = 0.5 # binary classification probability [0,1]. So default value is 0.5; THRESHOLD to buy order

    if CLASSIFICATION_TYPE == 3:
        PERCENT_UP = 0.005 # up signal % (if CLASSIFICATION_TYPE == 3)
        PERCENT_DOWN = 0.005 # down signal % (if CLASSIFICATION_TYPE == 3)

    MIN_ROWS_TO_ML = 50 # Minimum number of rows in the dataset to apply Machine Learning

    ## NORMALIZE DATA
    NORMALIZATION = {
        'enabled': True,
        'method': 'diff' # 'max', 'diff' or 'std'
    }

    ## MODEL HYPER PARAMETERS OPTIMIZATION
    OPTIMIZE_PARAMS = {
        'enabled': True, # Apply hyper model params optimization
        'iterations': 30, # Test dataframe size to optimize model params
        'n_evals': 10, # Number of evaluations to hyperopt
        'size': 100 # Test dataframe size to optimize model params
    }

    ## FEATURE MODEL VISUALIZATION: SHAP
    VISUALIZE_MODEL = {
        'enabled': True, # Apply hyper model params optimization
        'n_iterations': 50 # Test dataframe size to optimize model params
    }

    ## FEATURE SELECTION
    FEATURE_SELECTION = {
        'enabled': True, # Apply feature selection
        'n_iterations': 10, # Number of iterations to perform feature selection
        'method': 'embedded' # https://machinelearningmastery.com/an-introduction-to-feature-selection/ -> embedded | filter | wrapper
    }

    ## FEATURE ENGINEERING

    # Feature Engineering: dates
    FE_DATES = True # True to add dates feature engineering

    # Feature Engineering: tsfresh
    FE_TSFRESH = {
        'enabled': False,
        # 'method': MinimalFCParameters(), # https://tsfresh.readthedocs.io/en/latest/text/feature_extraction_settings.html -> MinimalFCParameters() | EfficientFCParameters() | ComprehensiveFCParameters()
        'window': 30,
    }

    # Feature Engineering: ta-lib
    FE_TA = {
        'enabled': True,
        'overlap': True,
        'momentum': True,
        'volume': True,
        'volatility': True,
        'price': True,
        'cycle': True,
        'pattern': True,
        'statistic': True,
        'math_transforms': False,
        'math_operators': False,
    }

    # Feature Engineering: https://github.com/bukosabino/ta
    FE_TA2 = True

    # Feature Engineering: fbprophet
    FE_FBPROPHET = {
        'enabled': False
    }

    # Feature Engineering: utils
    FE_UTILS = True

    ## CHECKS

    # Check if size test dataframe is less than total dataframe
    # assert OPTIMIZE_PARAMS['size'] < MIN_ROWS_TO_ML # TODO: check

    # Check if min rows is less than dataframe size.
    # assert MIN_ROWS_TO_ML <= DEFAULT_CONFIG['BARS'] # TODO restore check

    if CLASSIFICATION_TYPE == 2:
        # Check if threshold is in range [0,1]
        if THRESHOLD < 0.0 or THRESHOLD > 1.0:
            raise ValueError('THRESHOLD should be on [0,1] range.')
