# Kryptos Core

## About

The core service contains all the logic for running strategies.

## Installation

Follow the installation [instructions](../README.md#Installation) for the project.

## Using the core service

The functionality of the core service is exposed through various CLI commands for local development.

Each command simulates a trading strategy by running pre-built or dynamically built trading algorithms via [enigma-catalyst](https://github.com/enigmampc/catalyst).

Before running the commands, enter the worker container's shell

``` bash
$ docker-compose exec worker bash
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
  - Signals
  - ~Order Behavior~

These options can be defined via the CLI, JSON objects, the python API or a combination of the three interfaces.

### Running Strategies from the CLI

To run strategies from the CLI, use the `strat` command group

```bash
Usage: strat [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  build   Launch a strategy
  kill    Kill a running strategy
  stress  Launch multiple strategies

```

The main command is `build`. Take note of it's different options


``` bash
Usage: strat build [OPTIONS]

  Launch a strategy

Options:
  -ta, --market-indicators TEXT   Market Indicators listed in order of
                                  priority
  -ml, --machine-learning-models TEXT
                                  Machine Learning Models
  -d, --dataset [google|quandl]   Include asset in keyword list
  -c, --columns TEXT              Target columns for specified dataset
  -i, --data-indicators TEXT      Dataset indicators
  -f, --json-file TEXT
  -p, --python-script TEXT
  --paper                         Run the strategy in Paper trading mode
  --live                          Run the strategy in Live trading mode
  -a, --api                       Run the strategy locally via API
  -w, --worker                    Run the strategy locally inside an RQ worker
  -h, --hosted                    Run remotely on a GCP instance via the API
  --help                          Show this message and exit.
```

To create a strategy using TA indicators:
```bash
$ strat build -ta bbands -ta rsi
```

To use an external dataset:

Google Trends
```bash
$ strat build -d google -c 'bitcoin futures'
```

Quandle
```bash
$ strat build -d quandl -c 'MKTCP' -c 'NTRAN'
```

Calculate a basic indicator for external data
```bash
$ strat build -d google -c 'btc usd' -i 'relchange'
```

### Runing Machine Learning Strategies from the CLI

To create a strategy using ML models:
```bash
$ strat build -ml xgboost
$ strat build -ml lightgbm
$ strat build -ml lightgbm -ml xgboost # You buy if both models get buy signal and vice-versa.
```

You can get more details if you see the file: Kryptos/ml/README.md

### JSON Format
The `strat` command also accepts a JSON file. The JSON object represents all the inputs used to create a strategy. The JSON representation is displayed anytime the `strat` command is run, so you can use save it as a file and fine tune inputs such as indicator parameters.

Note that the QUOTE_CURRENCY must match the quote currency (2nd symbol) of the ASSET

For example:
```json
{
   "trading": {
     "EXCHANGE": "binance",
     "ASSET": "btc_usdt",
     "DATA_FREQ": "minute",
     "HISTORY_FREQ": "1T",
     "MINUTE_FREQ": "5",
     "MINUTE_TO_OPERATE": "1",
     "CAPITAL_BASE": 20000,
     "QUOTE_CURRENCY": "usdt",
     "START": "2018-8-10",
     "END": "2018-8-15",
     "BARS": 2000,
     "ORDER_SIZE": 0.5,
     "SLIPPAGE_ALLOWED": 0.02,
     "MAKER_COMMISSION": 0.0,
     "TAKER_COMMISSION": 0.0
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
         "symbol": "btc_usdt",
         "dataset": null,
         "label": "STOCH",
         "params": {
     }
      },
      {
         "name": "BBANDS",
         "symbol": "btc_usdt",
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
$ strat build -f examples/api_example.json
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
