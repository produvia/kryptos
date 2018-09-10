import os
import matplotlib.pyplot as plt
import shap

from ml.utils import get_algo_dir

def visualize_model(model, X, idx, configuration, namespace, name):
    if configuration['enabled'] and idx % configuration['iterations'] == 0:

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        shap.summary_plot(shap_values, X, plot_type="bar", show=False)

        # save files
        folder_path = get_algo_dir(namespace)
        f_path = os.path.join(folder_path, "{}_{}_analyze_features.png".format(name, idx))
        plt.savefig(f_path, bbox_inches="tight", dpi=300)

        # TODO: save in a image more results (weight, gain, etc)
        if name == 'XGBOOST':
            pass
        elif name == 'LIGHTGBM':
            pass
