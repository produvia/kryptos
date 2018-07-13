import operator
import random

def embedding_feature_selection(model, importance_type='all', percentage=0.9):
    """Perform feature selection using XGBoost embedded method.

    Args:
        model(xgboost.core.Booster): XGBoost model trained.
        importance_type(string):
            'weight' - the number of times a feature is used to split the data across all trees.
            'gain' - the average gain of the feature when it is used in trees.
            'cover' - the average coverage of the feature when it is used in trees.
            'all' - the number of times a feature is used to split the data across all trees.
        percentage(float): From 0 to 1, percentage of features to filter from total columns used.

    Returns:
        list: Name columns selected.
    """

    if importance_type == 'weight' or importance_type == 'all':
        used_cols_weight = _get_colums_score(model, 'weight')
        selected_cols = _get_percentage_selected_cols(used_cols_weight, percentage)

    if importance_type == 'gain' or importance_type == 'all':
        used_cols_gain = _get_colums_score(model, 'gain')
        selected_cols = _get_percentage_selected_cols(used_cols_gain, percentage)

    if importance_type == 'cover' or importance_type == 'all':
        used_cols_cover = _get_colums_score(model, 'cover')
        selected_cols = _get_percentage_selected_cols(used_cols_cover, percentage)

    if importance_type == 'all':
        lists = [used_cols_weight, used_cols_gain, used_cols_cover]
        used_cols = [x for t in zip(*lists) for x in t]
        used_cols = list(set(used_cols))
        selected_cols = _get_percentage_selected_cols(used_cols, percentage)

    return selected_cols


def _get_colums_score(model, importance_type):
    """Get columns used by XGBoost model ordered by importance.
    """
    importance = model.get_score(fmap='', importance_type=importance_type)
    importance = sorted(importance.items(), key=operator.itemgetter(1))
    used_cols = [x[0] for x in reversed(importance)]
    return used_cols


def _get_percentage_selected_cols(used_cols, percentage):
    """Get a percentage of best used columns.
    """
    num_columns = int(percentage*len(used_cols)/1.0)
    selected_cols = used_cols[0:num_columns]
    return selected_cols
