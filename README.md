# Kryptos

## Installation

Clone the repo:
```bash
$ git clone https://github.com/produvia/cryptocurrency-trading-platform.git
$ cd cryptocurrency-trading-platform
```

#### Install with [pipenv](https://github.com/pypa/pipenv#installation) (recommended):
```bash
$ pipenv install
```

or

#### Install with Docker
For a containerized installation: 
```bash
$ bash ./install_docker
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
$ docker exec -i -t kryptos_web_1 /bin/bash
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

### Running Stratgies from the CLI
```bash
Usage: strat [OPTIONS]

Options:
  -ta, --market-indicators TEXT  Market Indicators listed in order of priority
  -d, --dataset [google|quandl]  Include asset in keyword list
  -c, --columns TEXT             Target columns for specified dataset
  -i, --data-indicators TEXT     Dataset indicators
  -f, --json-file TEXT
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
strat.load_from_json(config)
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
"""Executed once after algorthim ends"""
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
A simple JSONRPC server is accessible to enable running strategies remotely.

First set up the flask app environment
```bash
$ export FLASK_APP=server/autoapp.py
$ export FLASK_DEVUG=1
```

Start the Server
```bash
$ flask run
```

To call the server, use the `strat` command in a seperate terminal
```bash
$ strat -ta macdfix --rpc
```

Note that vizualization will not be shown, and the response make take some time depending on the length of the trading period.

## Deployment with Docker

Install [Docker](https://docs.docker.com/compose/install/#prerequisites)(and Docker Compose)

For Linux:
```bash
$ sudo curl -L https://github.com/docker/compose/releases/download/1.21.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
$ sudo chmod +x /usr/local/bin/docker-compose
```

Start docker and Build the images
```bash
# this will take a while
$ bash ./init_docker.sh
```

Run `docker-compose up` to start start kryptos

To enter into the container's shell: 
`$ sudo docker exec -i -t kryptos_web_1 /bin/bash`


To stop everything:
`$ docker-compose stop`


## Running example (pre-built) strategies
This repo contains a set of [example catalyst trading strategies](crypto_platform/algos/). 

#### compare

Use the `compare` command to compare a select number of algos. 

```bash
$ compare [ALGOS]
```

The resulting percent return of each strategy is plotted against the benchmark.

The command optionally accepts metrics to compare via the `-m` flag, similar to with the `metrics` command

```bash
$ compare macdfix sma_crossover -m sharpe -m pnl
```

If no metrics are given the command defaults to the metrics enabled in *config.py*

#### compare_all_straegies
Use the `compare_all_straegies` command to run all exmaple strategies.

The portfolio of each strategy will be plotted against the benchmark.
The results will be saved to a new  *performance_results/* directory and include a csv file as well as a pickled pandas Dataframe object to be used comparison/analysis.

This command does not accept any arguments.

#### benchmark

The `benchmark` command will plot the percent return of a single algorithim against the benchmark of bitcoin price (*btc_usdt*)

```bash
$ benchmark ALGO_NAME
```


#### metrics

The `metrics` command will plot performance metrics over the trading period for a given algo.

If no metrics are specified, the metrics defined in _config.py_ will be used.

```bash
$ metrics ALGO_NAME
```

Optionally specify performance metrics via the `-m` flag
```bash
$ metrics buy_and_hodl -m sharpe -m sortino -m max_drawdown
```






