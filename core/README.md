# Kryptos

## About

Kryptos AI is a virtual investment assistant that manages your cryptocurrency portfolio. To learn more, check out the [Kryptos Slide Deck](https://docs.google.com/presentation/d/1O3BQ6fS9SuokJud8TZ1XPXX5QbjefAEiXNR3cxJIJwE/view) and the [Kryptos White Paper](https://docs.google.com/document/d/1Um9yoosEj-oZdEF3yMK2pt5TI0O2aRYhgkC0XJf_BVo/view).


## Installation


#### Install with [pipenv](https://github.com/pypa/pipenv#installation)
```bash
$ pipenv install
```

## Using the platform

The functionality of the paltform is exposed through various CLI commands.

Each command simulates a trading strategy by running pre-built or dynamically built trading algorithms via [enigma-catalyst](https://github.com/enigmampc/catalyst).

Before running the commands, ensure your virtualenv is activated:

If installed via pipenv:
```bash
$ pipenv shell
```

If installed via docker:
```bash
$ bash docker_scripts/dev-start.sh
```

### Configuration
There are 2 files used for configuration
  1. _crypto_platform/strategy/config.js_ -> Default trading strategy configuration
  2. _crypto_platform/settings.py_ -> General app behavior

## Strategies
The `Strategy` class acts as the interface for creating and running trading strategies as catalyst algorithms.
Running a strategy will by default run a backtest according to its trade config, produce plots visualizing performance and save a summary of its performance statistics.

Strategies are composed of a number of different inputs:
  - Trading Environment
  - Indicators
  - Datasets
  - ~Signals~
  - ~Order Behavior~

These options can be defined via the CLI, JSON objects, the python API or a combination of the three interfaces.

### Running Strategies from the CLI
```bash
Usage: strat [OPTIONS]

Options:
  -ta, --market-indicators TEXT  Market Indicators listed in order of priority
  -d, --dataset [google|quandl]  Include asset in keyword list
  -c, --columns TEXT             Target columns for specified dataset
  -i, --data-indicators TEXT     Dataset indicators
  -f, --json-file TEXT
  --paper                        Run the strategy in Paper trading mode
  --rpc                          Run the strategy via JSONRPC
  -h, --hosted                   Run via rpc using remote server
  --help                         Show this message and exit.
```

To create a strategy using TA indicators:
```bash
$ strat -ta bbands -ta rsi
```

To use an external dataset:

Google Trends
```bash
$ strat -d google -c 'bitcoin futures'
```

Quandle
```bash
$ strat -d quandl -c 'MKTCP' -c 'NTRAN'
```

Calculate a basic indicator for external data
```bash
$ strat -d google -c 'btc usd' -i 'relchange'
```

### Runing Machine Learning Strategies from the CLI

To create a strategy using ML models:
```bash
$ strat -ml xgboost
$ strat -ml lightgbm
$ strat -ml lightgbm -ml xgboost # You buy if both models get buy signal and vice-versa.
```

By default, Machine Learning models use:
  * MIN_ROWS_TO_ML -> Minimum number of rows in the dataset to apply Machine Learning

  * CLASSIFICATION_TYPE -> Labeling type:
      1. Regression
      2. Binary Classification (DOWN / UP)
      3. Multiclass Classification (DOWN / KEEP / UP)

  * STOP_LOSS -> Percentage to Stop-Loss
  * TAKE_PROFIT -> Percentage to Take-Profit
  * NORMALIZATION -> True to set up data normalizated; False don't set up. Also, you can select the method to use ('max', 'diff' or 'std').


#### Feature Engineering techniques

Using dates features, tsfresh, fbprophet and technical analysis (ta-lib) libraries.

You need to set the next setting variables:
  * FE_DATES -> True to add dates features; False don't add any feature.
  * FE_TSFRESH -> True to add tsfresh features; False don't add any feature.
  * FE_TA -> True to add ta features; False don't add any feature.
  * FE_FBPROPHET -> True to add fbprophet features; False don't add any feature.
  * FE_UTILS -> True to add utils features; False don't add any feature.


#### Hyper parameters optimization

Using Hyperopt library.

You need to set the OPTIMIZE_PARAMS setting variable:
  * 'enabled' -> True to apply hyper model params optimization; False don't apply.
  * 'iterations' -> Test dataframe size to optimize model params
  * 'n_evals' -> Number of evaluations to hyperopt
  * 'size' -> Test dataframe size to optimize model params

#### Feature Selection techniques

Using embedded, filter and wrapper methods: https://machinelearningmastery.com/an-introduction-to-feature-selection/

You need to set the FEATURE SELECTION setting variable:

  * 'enabled' -> Apply feature selection
  * 'n_iterations' -> Number of iterations to perform feature selection
  * 'method' -> https://machinelearningmastery.com/an-introduction-to-feature-selection/ -> embedded | filter | wrapper

Also, you can add external datasets as features too (to work with daily frequency only):

Google Trends
```bash
$ strat -d google -c "bitcoin" -c "btc" -ml xgboost
or
$ strat -ml xgboost -d google -c "bitcoin" -c "btc"
```

Quandle
```bash
$ strat -d quandl -c 'MKTCP' -c 'NTRAN' -ml xgboost
or
$ strat -ml xgboost -d quandl -c 'MKTCP' -c 'NTRAN'
```

### JSON Format
The `strat` command also accepts a JSON file. The JSON object represents all the inputs used to create a strategy. The JSON representation is displayed anytime the `strat` command is run, so you can use save it as a file and fine tune inputs such as indicator parameters.

For example:
```json
{
   "trading": {
      "EXCHANGE": "bitfinex",
      "ASSET": "btc_usd",
      "DATA_FREQ": "daily",
      "HISTORY_FREQ": "1d",
      "CAPITAL_BASE": 5000,
      "BASE_CURRENCY": "usd",
      "START": "2017-10-10",
      "END": "2018-3-28"
   },
   "datasets": [
      {
         "name": "google",
         "columns": [
            "bitcoin futures"
         ],
         "indicators": [
            {
               "name": "RELCHANGE",
               "symbol": "bitcoin futures",
               "dataset": "google",
               "label": "RELCHANGE",
               "params": {}
            }
         ]
      }
   ],
   "indicators": [
      {
         "name": "STOCH",
         "symbol": "btc_usd",
         "dataset": null,
         "label": "STOCH",
         "params": {
     }
      },
      {
         "name": "BBANDS",
         "symbol": "btc_usd",
         "dataset": null,
         "label": "BBANDS",
         "params": {
            "matype": "DEMA",
            "timeperiod": 30
         }
      }
   ]
}
```

To run a strategy from the file:
```bash
$ strat -f examples/api_example.json
```

### Python API

#### Basics

Create a strategy object
```python
from crypto_platform.strategy import Strategy

strat = Strategy('MyStrategy')
```

Optionally load JSON config
```
config = './sma_crossover.json'
strat.load_json_file(config)
```

Run the strategy
```python
strat.run()
```

Attach indicators
```python
from crypto_platform.strategy.indicators import technical

# first create indicators
bbands = technical.get_indicator('BBANDS')
stoch = technical.get_indicator('STOCH')

# override default params
bbands.update_param('matype', 'EMA')

# attach indicators to strategy
strat.add_market_indicator(bbands)
strat.add_market_indicator(stoch)
```

Use External Datadets
```python
from crypto_platform.strategy.indicators import basic

strat.use_dataset('quandl', columns=['MKTCP'])

strat.use_dataset('google', columns=['bitcoin futures'])
strat.add_data_indicator('google', 'relchange', col='bitcoin futures')
```

#### Decorators

The `Strategy` object provides a set of decorators used to define logic to specific moments in the algorithm lifespan.

Define setup and processing logic
```
@strat.init
def init(context):
"""Set up strategy once before trading begins"""
    context.i = 0

@strat.handle_data
def handle_data(context, data):
"""Executed at every new trading step"""
    context.i += 1

@strat.analyze()
def analyze(context, results, pos):
"""Executed once after algorithm ends"""
    print('Completed for {} trading periods'.format(context.i))

```

Define buy and sell signals
```python
from crypto_paltform.strategy.signals import utils

@strat.signal_sell
def my_sell_signal(context, data):
  """Defines condition to signal sell"""
  return utils.cross_below(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)

@strat.signal_buy
def signal_buy(context, data):
"""Defines condition to signal buy"""
    return utils.cross_above(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)
  ```

## JSONRPC Server

A simple JSONRPC server is accessible to enable running strategies remotely. Simply add the `--rpc` flag to the `strat` command

### Remote Server
To use the hosted server on Google Cloud Platform, add the `-h` (hosted) flag

```bash
$ strat -ta macdfix --rpc -h
```


### Using the local server

#### Inside Docker
If you are using docker, there is no setup needed. Simply add the `--rpc` flag.

```bash
$ strat -ta macdfix --rpc
```

#### Outside Docker

If running outside of Docker, first set up the flask app environment
```bash
$ export FLASK_APP=autoapp.py
$ export FLASK_DEBUG=1
$ export FLASK_ENV=development
```

Then start the server
```bash
$ flask run
```

Then use the `strat` command in a seperate terminal
```bash
$ strat -ta macdfix --rpc
```

Note that vizualization will not be shown when using `--rpc`


## Using Docker

### Local development

Install [Docker](https://docs.docker.com/compose/install/#prerequisites)(and Docker Compose)

Build the containers

`$ bash docker_scripts/dev-build.sh`

Run and connect to the containers

`$ bash docker_scripts/dev-start.sh`

To stop everything
```bash
$ docker-compose stop
```

### Deploy to Google Cloud Platform

Connect to the Google Cloud Compute instance

```
gcloud compute --project "kryptos-204204" ssh --zone "us-west1-a" "kryptos-compose"
```

#### Initial instance setup
Ensure firewall allows http on port 80

Because the app runs on a containerized OS, we need to use the docker-compose *image* inside docker instead of installing

```bash
$ docker run docker/compose:1.13.0 version
```

then make an alias

```bash
$ echo alias docker-compose="'"'docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/rootfs/$PWD" \
    -w="/rootfs/$PWD" \
    docker/compose:1.13.0'"'" >> ~/.bashrc
```

docker-compose should now be accessible

Next, configure docker to pull from GCR

```bash
docker-credential-gcr configure-docker
```

#### Run for production

Pull the latest changes from github or use gcloud to scp the repo

```bash
gcloud compute scp . kryptos-compose:~/kryptos --recurse
```

build the images

```bash
$ bash docker_scripts/prod-build.#!/bin/sh
```

Start the containers with docker-compose

```bash
$ docker-compose up -d
```

Download exchange data

```bash
$ bash docker_scripts/ingest.sh
```

Test deployment using rpc from local machine

```
$ strat -ta macd --rpc -h
```
