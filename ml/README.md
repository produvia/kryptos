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


#### Feature Exploration techniques

We use plot_importance methods of XGBoost and LightGBM to explore in detail the feature importance in the models. Also, we use 'shap library' to get more information.

You can set the VISUALIZE_MODEL setting variable:

  * 'enabled' -> Apply feature Exploration
  * 'n_iterations' -> Number of iterations to get detailed information.


#### Extra datasets

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


#### Data pre visualization

We generate profile reports from a pandas DataFrame using pandas-profiling tool.

You can set the PROFILING_REPORT setting variable:

  * 'enabled' -> Apply feature Exploration
  * 'n_iterations' -> Number of iterations to visualize input data.

#### Results

TODO: talk about confussion matrix...
