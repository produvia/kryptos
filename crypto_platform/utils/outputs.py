import sys
import os
from os.path import basename


def dump_to_csv(filename, results, context=None):
    results.to_csv(filename)