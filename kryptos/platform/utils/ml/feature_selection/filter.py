from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression# , mutual_info_regression


def filter_feature_selection(X, y, percentage=0.8):
    """Apply a statistical measure to assign a scoring to each feature, features
    are ranked by the score.
    Consider each feature independently / with regard to the dependent variable (class value).

    Args:
        X(pandas.DataFrame): Features columns.
        y(pandas.DataFrame): Target column.
        percentage(float): From 0 to 1, percentage of features to filter from total columns used.

    Returns:
        list: Name columns selected.
    """
    if percentage > 1.0 or percentage < 0.0:
        raise ValueError("'percentage' value is not valid [0, 1]")
        
    kBest = int(percentage*len(X.columns)/1.0)

    test = SelectKBest(score_func=f_regression, k=kBest)
    fit = test.fit(X, y)

    # Summarize scores
    features = fit.transform(X)

    selected_cols = fit.get_support(indices=True)

    return list(X[selected_cols].columns.values)
