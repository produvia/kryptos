# Kryptos Quickstart

This guide will walk through the basic workflow for creating strategies with kryptos.

## Strategy creation workflow

Kryptos provides three interfaces for creating strategies

1. Passing strategy parameters via CLI options
2. From a JSON representation
3. Using the python api

In general, you will use all three interfaces to build and imporve strategies.
Let's walk through the basic workflow

### Using the strat CLI

Start by running the `strat` command with a technical indicator

```bash
$ strat -ta macdfix
```

You will see the following JSON structure output in the console

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
   "datasets": [],
   "indicators": [
      {
         "name": "MACDFIX",
         "symbol": "btc_usd",
         "dataset": null,
         "label": "MACDFIX",
         "params": {
            "signalperiod": 9
         }
      }
   ],
   "signals": {}
}
```

This structure represents all the strategy inputs that can be modified.
Copy the JSON to save it to a new file in *examples/mystrategy.json*. We will use this file as a scratchpad to modify the strategy.

### Loading strategies from JSON
Every time the `strat` command is run, the strategy's inputs are dumped to JSON.
We can use this JSON to either save a strategy or to modify it.

To run the strategy we just created, we could run

```strat -f examples/mystrategy.json```

This would give us the same performace as with the first command using `-ta`


Lets change the signalperiod used to calculate the MACDFIX indicator from 9 to 4.

```json
"indicators": [
   {
      "name": "MACDFIX",
      "symbol": "btc_usd",
      "dataset": null,
      "label": "MACDFIX",
      "params": {
         "signalperiod": 4
      }
   }
]
 ```

We now load the strategy using the `-f` option

```bash
$ strat -f example/mystrategy.json
```

Alright! That change made our strategy perform better and make a small profit.

Let's try adding a few more indicators. Note that if we were to run `strat -ta macdfix` again, instead of loading the file, the JSON output would use the default *signalperiod*.

In order to preserve our modifications to the JSON structure, we can add additional indicators like so

```bash
$ strat -f examples/mystrategy.json -ta bbands -ta ema -ta sma
```

Notice that the JSON output now includes the new indicators and their default parameter values, but still contains the modified *signalperiod*.

```json
"indicators": [
    {
       "name": "MACDFIX",
       "symbol": "btc_usd",
       "dataset": null,
       "label": "MACDFIX",
       "params": {
          "signalperiod": 4
       }
    },
    {
       "name": "SMA",
       "symbol": "btc_usd",
       "dataset": null,
       "label": "SMA",
       "params": {
          "timeperiod": 30
       }
    },
    {
       "name": "EMA",
       "symbol": "btc_usd",
       "dataset": null,
       "label": "EMA",
       "params": {
          "timeperiod": 30
       }
    },
    {
       "name": "BBANDS",
       "symbol": "btc_usd",
       "dataset": null,
       "label": "BBANDS",
       "params": {
          "timeperiod": 5,
          "nbdevup": 2,
          "nbdevdn": 2,
          "matype": 0
       }
    }
 ]
```

We can now copy and save this new JSON structure to the *mystrategy.json* file. And continue to iterate on the strategy parameters.

For instance, we can adjust the dates to run the strategy.

```json
"trading": {
   "EXCHANGE": "bitfinex",
   "ASSET": "btc_usd",
   "DATA_FREQ": "daily",
   "HISTORY_FREQ": "1d",
   "CAPITAL_BASE": 5000,
   "BASE_CURRENCY": "usd",
   "START": "2016-10-10",
   "END": "2018-3-28"
}
```

### Python API
Its very likely that as you improve your strategy, you will want to implement additional logic or define your own signals instead of an indicator's default.

The kyrptos python library provides a simple api to extend upon the CLI and JSON interfaces.

Start by creating a strategy object

```python
from kryptos.strategy import Strategy

import logbook

strat = Strategy('mystrategy', data_frequency='daily')
```

Load the JSON file to extend upon our existing strategy
```python

config = './mystrategy.json'
strat.load_from_json(config)
```

Let's add an additional indicator

```Python
from kryptos.strategy.indicators import technical

stoch = technical.get_indicator('STOCH')
strat.add_market_indicator(stoch)
```

Stratgy config can be set or override JSON values
```python
strat.trading_info['CAPITAL_BASE'] = 10000
```

Add this to the end of the file to setup the strategy to be run

```python
if __name__ == '__main__':
    # dump the json representation
    log.info('Strategy Schema:\n{}'.format(strat.serialize()))
    strat.run()
```
Save the file as *examples/mystrategy.py*

The strategy can now be run as a python script, instead of the using the `strat` command.

```bash
$ python examples/mystrategy.py
```


#### Extending the strategy with custom logic


There are three points in the algorithm lifecycle where you can add your own custom logic: Before the algo starts, after each algo iteration, and when the trading period has ended.

Logic can be executed here by using the following decorators
```python

@strat.init
def startup_logic(context):
  # set up anything you need before the algo starts
  context.day = 0

@strat.handle_data
def process_current_algo_state(context, data):
  context.day += 1
  if context.day == 50
    # use SMA after trading for 50 days
    sma = technical.get_indicator('SMA')
    strat.add_market_indicator(sma)

# specify number of custom plots if creating plots
@strat.analyze(num_plots=0)
def print_overview(context, results, pos):
    # trading has finished, and results are available
    ending_cash = results.cash[-1]
    print('Ending cash: ${}'.format(ending_cash))
    print('Completed for {} trading periods'.format(context.i))
```

Additionally, buy and sell signals can be defined with the following decorators.
These functions are called every iteration and should return a boolean.
Returning `True` adds 1 point to the order type signal count.

The Strategy object will create a buy or sell order if the signal count for one order type is greater than the other.

```Python
from kryptos.strategy.signals import utils

@strat.signal_sell
def signal_sell(context, data):
  # signal sell if the fast line crosses below the slow line
  return utils.cross_below(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)


@strat.signal_buy
def signal_buy(context, data):
    # signal sell if the fast line crosses above the slow line
    return utils.cross_above(sma_fast.outputs.SMA_FAST, sma_slow.outputs.SMA_SLOW)
```
