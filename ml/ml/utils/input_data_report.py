import pandas_profiling
import os

from ml.utils import get_algo_dir

def profile_report(df, idx, namespace, name, configuration):
    if configuration['enabled'] and idx % configuration['n_iterations'] == 0:
        profile = pandas_profiling.ProfileReport(df)
        folder = os.path.join(namespace, 'profiling_report')
        folder_path = get_algo_dir(folder)
        f_path = os.path.join(folder_path, "profiling_report_model_{}_id_{}_with_{}_columns.html".format(name, idx, len(df.columns)))
        profile.to_file(outputfile=f_path)
