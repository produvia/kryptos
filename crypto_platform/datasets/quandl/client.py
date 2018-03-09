import os
import csv
import quandl

from crypto_platform.config import CONFIG
import matplotlib.pyplot as plt

API_KEY = os.getenv('QUANDL_API_KEY')
quandl.ApiConfig.api_key = API_KEY


def codes_from_csv():
    codes = []
    csv_file = os.path.join(os.curdir, 'BCHAIN-datasets-codes.csv')
    with open(csv_file, 'r') as f:
        for i in csv.reader(f):
            codes.append(i[0])

    return codes


def fetch_datasets(codes, start_date=None, end_date=None, collapse=None, transformation=None, rows=None):
    """Retrieves datasets provides by list of codes (DATABASE/DATASET)

    https://docs.quandl.com/docs/parameters-2

    Returns pandas Dataframe
    """

    codes = codes_from_csv()
    df = quandl.get(codes)
    return df


def clean_dataframe(df):
    df = df.rename(columns=lambda x: x.replace('BCHAIN/', ''))
    df = df.rename(columns=lambda x: x.replace(' - Value', ''))
    df['Symbol'] = 'btc'
    return df


def fetch_all():
    codes = codes_from_csv()
    df = fetch_datasets(codes)
    df = clean_dataframe(df)
    df.to_csv('data.csv', mode='w')


if __name__ == '__main__':
    fetch_all()
