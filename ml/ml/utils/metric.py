import os
import time
from sklearn.metrics import confusion_matrix, classification_report, cohen_kappa_score, accuracy_score

from ml.utils import get_algo_dir

def classification_metrics(namespace, file_name, y_true, y_pred, extra_results, y_pred_proba=False):
    target_names = ['KEEP', 'UP', 'DOWN']
    algo_dir = get_algo_dir(namespace)
    f_path = os.path.join(algo_dir, file_name)

    # Check solution and prediction size
    assert len(y_true) == len(y_pred)

    if len(y_true) > 0 and len(y_pred):
        with open(f_path, "a") as f:
            f.write(time.strftime("%Y/%m/%d %H:%M:%S") + '\n')
            f.write('Date Start: {}'.format(extra_results['start']) + '\n')
            f.write('Date End: {}'.format(extra_results['end']) + '\n')
            f.write('Minute Frequency: {}'.format(extra_results['minute_freq']) + '\n')
            f.write('Accuracy: {}'.format(accuracy_score(y_true, y_pred)) + '\n')
            f.write('Coefficient Kappa: {}'.format(cohen_kappa_score(y_true, y_pred)) + '\n')
            f.write('Classification Report:' + '\n')
            f.write(classification_report(y_true, y_pred, target_names=target_names))
            f.write("Confussion Matrix:" + '\n')
            f.write(str(confusion_matrix(y_true, y_pred)))
            f.write('\n')
            f.write('Return Profit Percentage: {}'.format(extra_results['return_profit_pct']) + '\n')
            f.write('Sharpe Ratio: {}'.format(extra_results['sharpe_ratio']) + '\n')
            f.write('Sortino Ratio: {}'.format(extra_results['sortino_ratio']) + '\n')
            f.write('Sharpe Ratio (Bitcoin Benchmark): {}'.format(extra_results['sharpe_ratio_benchmark']) + '\n')
            f.write('Sortino Ratio (Bitcoin Benchmark): {}'.format(extra_results['sortino_ratio_benchmark']) + '\n')
            f.close()
