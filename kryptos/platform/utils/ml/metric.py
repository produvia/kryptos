from sklearn.metrics import *

# TODO: eliminar el último...
def classification_metrics(y_true, y_pred, y_pred_proba=False):
    target_names = ['KEEP', 'UP', 'DOWN']
    if y_pred_proba is not False:
        print('Cross Entropy: {}'.format(log_loss(y_true, y_pred_proba)))
    print('Accuracy: {}'.format(accuracy_score(y_true, y_pred)))
    print('Coefficient Kappa: {}'.format(cohen_kappa_score(y_true, y_pred)))
    print('Classification Report:')
    print(classification_report(y_true.values, y_pred, target_names=target_names))
    print("Confussion Matrix:")
    print(confusion_matrix(y_true, y_pred))
