# Cryptocurrency Trading Platform

## Installation

Strongly reccomended to **create a virtual environment**
```
pip install virtualenv
virtualenv crypto-platform
source ./crypto-platform/bin/activate

```

Install dependencies (This may take a while)

`pip install -r requirements.txt`

Then install this library

`pip install -U -e .`


## Using the library
The libray currently contains the following CLI commands

#### compare_all
Running `compare_all` will use produce a plot comparing the portfolio value of all strategies in the *algos/* directory. The results will be saved to *scripts/performance_results_* and include a csv file as well as a pickled pandas Dataframe object to be used comparison/analysis.


The results are not yet standardized, but instead record the data specified by each algorithim.

#### benchmark

Running `benchmark <algo_name>` will plot the percent return of a given algorithim against the benchmark of bitcoin price (*btc_usdt*)

Available algorithm names include:

- bear_market: Sell off asset if price is more than 20% lower than highest highest closing-price over 2 month period. Invest 90% of portfolio if price is more than 20% higher than lowest closing priceover 2 month period
- buy_and_hodl: Buy 80% of portfolio of an asset and hodl!
- buy_low_sell_high
- dual_moving_average
- mean_reversion_simple
- rsi
- simple_loop
- talib_sample



