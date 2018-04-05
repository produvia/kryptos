import os
import json

CURRENT_DIR = os.path.dirname(__file__)
DEFAULT_CONFIG_FILE = os.path.abspath(os.path.join(CURRENT_DIR, './config.json'))

with open(DEFAULT_CONFIG_FILE, 'r') as f:
    DEFAULT_CONFIG = json.load(f)



from crypto_platform.strategy.strategy import Strategy

