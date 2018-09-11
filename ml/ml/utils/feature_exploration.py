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

        # save files
        folder_path = get_algo_dir(namespace)
        f_path = os.path.join(folder_path, "{}_{}_analyze_shap_features.png".format(name, idx))
        plt.savefig(f_path, bbox_inches="tight", dpi=300)

        if name == 'XGBOOST':
            # TODO: exportar codigo a una función.
            importance_type = 'weight'
            xgb.plot_importance(model, importance_type=importance_type, max_num_features=20)
            folder_path = get_algo_dir(namespace)
            f_path = os.path.join(folder_path, "{}_{}_analyze_xgboost_{}_features.png".format(name, idx, importance_type))
            plt.savefig(f_path, bbox_inches="tight", dpi=300)

            importance_type = 'cover'
            xgb.plot_importance(model, importance_type=importance_type, max_num_features=20)
            folder_path = get_algo_dir(namespace)
            f_path = os.path.join(folder_path, "{}_{}_analyze_xgboost_{}_features.png".format(name, idx, importance_type))
            plt.savefig(f_path, bbox_inches="tight", dpi=300)

            importance_type = 'gain'
            xgb.plot_importance(model.get_score(fmap='', importance_type=importance_type), importance_type=importance_type, max_num_features=20)
            folder_path = get_algo_dir(namespace)
            f_path = os.path.join(folder_path, "{}_{}_analyze_xgboost_{}_features.png".format(name, idx, importance_type))
            plt.savefig(f_path, dpi="figure")

        elif name == 'LIGHTGBM':

            importance_type = 'split'
            lgb.plot_importance(model, importance_type=importance_type, max_num_features=20)
            folder_path = get_algo_dir(namespace)
            f_path = os.path.join(folder_path, "{}_{}_analyze_lightgbm_{}_features.png".format(name, idx, importance_type))
            plt.savefig(f_path, bbox_inches="tight", dpi=300)

            importance_type = 'gain'
            lgb.plot_importance(model, importance_type=importance_type, max_num_features=20)
            folder_path = get_algo_dir(namespace)
            f_path = os.path.join(folder_path, "{}_{}_analyze_lightgbm_{}_features.png".format(name, idx, importance_type))
            plt.savefig(f_path, bbox_inches="tight", dpi=300)

        else:

            pass
