import os
import matplotlib.pyplot as plt
import xgboost as xgb
import lightgbm as lgb
import shap

from ml.utils import get_algo_dir


def visualize_model(model, X, idx, configuration, namespace, name):

    if configuration['enabled'] and idx % configuration['iterations'] == 0:

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        shap.summary_plot(shap_values, X, plot_type="bar", show=False)
        save_fig(namespace, name, idx, importance_type='shap')

        if name == 'XGBOOST':
            for i in ['weight', 'cover', 'gain']:
                if i == 'gain':
                    xgb.plot_importance(model.get_score(fmap='', importance_type=i), importance_type=i, max_num_features=20)
                else:
                    xgb.plot_importance(model, importance_type=i, max_num_features=20)
                save_fig(namespace, name, idx, importance_type=i)

        elif name == 'LIGHTGBM':
            for i in ['split', 'gain']:
                lgb.plot_importance(model, importance_type=i, max_num_features=20)
                save_fig(namespace, name, idx, importance_type=i)

        else:
            pass

# TODO: fusion with Cam method
def save_fig(namespace, name, idx, importance_type):

    # TODO: meter carpeta intermedia "feature_exploration"

    folder_path = get_algo_dir(namespace)
    f_path = os.path.join(folder_path, "{}_{}_analyze_{}_features.png".format(name, idx, importance_type))

    if importance_type == 'gain' and name == 'XGBOOST':
        plt.savefig(f_path, dpi='figure')
    else:
        plt.savefig(f_path, bbox_inches="tight", dpi=300)
