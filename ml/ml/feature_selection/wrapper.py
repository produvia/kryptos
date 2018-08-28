from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier

def wrapper_feature_selection(X, y, percentage=0.8):
    """A predictive model is used to evaluate a combination of features and
    assign a score based on model accuracy.

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

    classifier = RandomForestClassifier()
    rfe = RFE(classifier, n_features_to_select=kBest)
    rfe.fit(X, y)

    features_sorted_by_rank = sorted(zip(map(lambda x: round(x, 4), rfe.ranking_), X.columns))
    used_cols = [x[1] for x in features_sorted_by_rank[:kBest]]

    return used_cols
