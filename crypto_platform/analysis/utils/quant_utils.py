import datetime

def log_error(err_file, err_msg):
    with open(err_file, 'a') as f:
        f.write('-'*15 + '\n')
        f.write(str(datetime.datetime.now()) + '\n')
        f.write(str(err_msg) + '\n')