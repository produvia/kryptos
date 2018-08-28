import pandas as pd
import itertools

from ml.utils.feature_selector import FeatureSelector


def lgb_embedded_feature_selection(X_train, y_train):
    """Perform feature selection using LightGBM embedded method:
    https://github.com/WillKoehrsen/feature-selector
    https://towardsdatascience.com/a-feature-selection-tool-for-machine-learning-in-python-b64dd23710f0
    https://github.com/WillKoehrsen/feature-selector/blob/master/Feature%20Selector%20Usage.ipynb

    Returns:
        list: Name columns selected.
    """

    fs = FeatureSelector(data=X_train, labels=y_train)

    fs.identify_missing(missing_threshold=0.6)
    # fs.identify_single_unique() # NOTE: Pandas version 0.23.4 required
    fs.identify_collinear(correlation_threshold=0.995) # 0.98
    fs.identify_zero_importance(task = 'regression', eval_metric = 'mse',
                                n_iterations = 10, early_stopping = True)
    fs.identify_low_importance(cumulative_importance = 0.99)

    excl = []
    excl = [i for i in itertools.chain(*itertools.zip_longest(excl,
                            fs.ops['missing'], fs.ops['collinear'],
                            fs.ops['zero_importance'], fs.ops['low_importance'])) if i is not None]

    selected_cols = [c for c in X_train.columns if c not in excl]

    return selected_cols
