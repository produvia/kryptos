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
  - Signals
  - ~Order Behavior~

These options can be defined via the CLI, JSON objects, the python API or a combination of the three interfaces.

### Running Strategies from the CLI
```bash
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
  -a, --api                       Run the strategy via API
  -w, --worker                    Run the strategy inside an RQ worker
  -h, --hosted                    Run on a GCP instance via the API
  --help
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

You can get more details if you see the file: Kryptos/ml/README.md

### JSON Format
The `strat` command also accepts a JSON file. The JSON object represents all the inputs used to create a strategy. The JSON representation is displayed anytime the `strat` command is run, so you can use save it as a file and fine tune inputs such as indicator parameters.

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
     "QUOTE_CURRENCY": "usd",
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
