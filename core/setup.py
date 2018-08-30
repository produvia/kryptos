#!/usr/bin/env python
import os
from setuptools import setup, find_packages

__version__ = "0.1.2"

#
# See https://packaging.python.org/requirements/  and
# https://caremad.io/posts/2013/07/setup-vs-requirement/  for more details.
requires = [
    'enigma-catalyst',
    'matplotlib',
    'TA-Lib',
    'quandl',
    'click',
    'logbook'
]


def package_files(directory):
    for path, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.join('..', path, filename)


package_name = "kryptos"
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
        bchain=kryptos.scripts.bchain_activity:run
        trends=kryptos.scripts.trends:run
        strat=kryptos.scripts.build_strategy:run
        compare_all_ta=kryptos.scripts.run_all_ta:run
        workers=kryptos.worker.worker:manage_workers
        stress=kryptos.scripts.stress_worker:run
    ''',
    zip_safe=False,
)
