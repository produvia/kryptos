#!/usr/bin/env python

import os
from crypto_platform import __version__
from setuptools import setup, find_packages

#
# See https://packaging.python.org/requirements/  and
# https://caremad.io/posts/2013/07/setup-vs-requirement/  for more details.
requires = [
    'enigma-catalyst',
    'matplotlib',
    'TA-Lib',
    'quandl',
    'Click'
]


def package_files(directory):
    for path, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.join('..', path, filename)


package_name = "crypto-trading_platform"
base_dir = os.path.abspath(os.path.dirname(__file__))
# Get the long description from the README file
with open(os.path.join(base_dir, 'README.md'), 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(
    name=package_name,
    version=__version__,
    author="Produvia",
    author_email="hello@produvia.com",
    url="https://produvia.com",
    description="AI-Driven Cryptocurrency Trading Platform",
    long_description=long_description,
    keywords="cryptocurrency AI algorithmic trading",
    # license='MIT',
    packages=find_packages(base_dir),
    install_requires=requires,
    entry_points='''
        [console_scripts]
        benchmark=crypto_platform.scripts.run_benchmark:benchmark
        compare_all_strategies=crypto_platform.scripts.run_strategies:run
        metrics=crypto_platform.scripts.run_metrics:run
        compare=crypto_platform.scripts.compare:run
        ta=crypto_platform.scripts.run_ta:run
        bchain=crypto_platform.scripts.bchain_activity:run
    ''',
    zip_safe=False,
)

   