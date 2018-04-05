# Cryptocurrency Trading Platform

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

#### Optionally install with pip:

Create virtualenv
```bash
$ pip install virtualenv
$ virtualenv venv
$ source ./venv/bin/activate
```

Install package as editable
```bash
$ pip install -e .
```


## Using the platform

The functionality of the paltform is exposed through various CLI commands.

Each command simulates a trading strategy by running pre-built or dynamically built trading algorithms via [enigma-catalyst](https://github.com/enigmampc/catalyst). The algorithm(s) will run using global configuration values and  plot various measurements of the algorithms performance.

Before running the commands, ensure your virtualenv is activated:

If installed via pipenv:
```bash
$ pipenv shell
```

If installed via virtualenv/pip:
```bash
$ source ./venv/bin/activate
```

### Configuration
Global algorithm behavior can be adjusted by modifying the values in [crypto_platform/config.json](/crypto_platform/config.py). These parameters (asset, exchange, start, end, etc...) are useful standardizng strategy performance.

## Strategies
The `Strategy` class acts as the interface for creating and running trading strategies as catalyst algorithms.

#### Running Stratgies from the CLI
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

#### JSON Format
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
$ strat -f api_example.json
```



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

## Running Dynamic Stragies
The following commands run algorithms requiring input parameters that effect their trading logic. These strategies contain a basic skeleton to iterate through the algorithm but tradng decisions are determined by analyses specified indicators of the respective dataset.

#### Technical Analysis
Use the `ta` command to run a strategy using Technical Analysis of specified market indicators.

```bash
$ ta -i bbands
```

use multiple indicators
```bash
$ ta -i bbands -i psar
```

Optionally enter the market on the first iteration
```bash
$ ta -i obv -e
```


#### Blockchain Activity

The `bchain` command is used to create a trading strategy by analyzing Quandl's [Blockchain Database](https://www.quandl.com/data/BCHAIN-Blockchain).

This database is split into datasets which can be specified via their [codes](/crypto_platform/datasets/quandl_data/BCHAIN-datasets-codes.csv) using the `-s` flag.

For example, to use Number of Transactions Per Day:
```bash
$ bchain -s NTRAN
```

To view Miners' Revenue and Bitcoin Difficulty
```bash
$ bchain -s MIREV -s DIFF
```

Note: `bchain` does not yet peform trade logic and only visualizes the dataset

#### Google Search Trends

The `trends` command is used to create a strategy by analyzing interest over time in terms of Google Trends search volume.

Simply provide one or more seach terms:

```bash
$ trends btc ethereum litecoin
```

Or for terms that include spaces:
```bash
$ trends btc litecoin 'litecoin vs bitcoin'
```

Optionally provide the `-a` to include the algorithm's asset (for example btc_usd) as a search term





