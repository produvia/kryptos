# Cryptocurrency Trading Platform

## Installation

Strongly reccomended to **create a virtual environment**
```
pip install virtualenv
virtualenv crypto-platform
source ./crypto-platform/bin/activate

```

Then install this library

`pip install -e .`

(It may take a while to install catalyst and it's dependencies)

## Using the library
Currently there is only a single script used to run the algorithims found in *crypto_platform/algos/single_asset/*

The script runs each strategy using the config values found in `scripts/config.py`

```
cd scripts
python run_strategies.py
```

The results will be saved to *scripts/performance output* and include a csv file as well as a pickled pandas Dataframe object to be used comparison/analysis.

The results are not yet standardized, but instead record the data specified by each algorithim.