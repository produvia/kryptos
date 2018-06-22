import os
from sklearn.metrics import *
from kryptos.platform.utils.outputs import get_algo_dir

def classification_metrics(namespace, file_name, y_true, y_pred, y_pred_proba=False):
    target_names = ['KEEP', 'UP', 'DOWN']
    algo_dir = get_algo_dir(namespace)
    f_path = os.path.join(algo_dir, file_name)

    with open(f_path, "a") as f:
        f.write('Accuracy: {}'.format(accuracy_score(y_true, y_pred)) + '\n')
        f.write('Coefficient Kappa: {}'.format(cohen_kappa_score(y_true, y_pred)) + '\n')
        f.write('Classification Report:' + '\n')
        f.write(classification_report(y_true, y_pred, target_names=target_names))
        f.write('\n')
        f.write("Confussion Matrix:" + '\n')
        f.write(str(confusion_matrix(y_true, y_pred)))
        f.write('\n')
        f.close()
