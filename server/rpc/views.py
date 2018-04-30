# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import json
from flask import Blueprint
from server.extensions import jsonrpc
from crypto_platform.strategy import Strategy

api = Blueprint('api', __name__)



@jsonrpc.method('Strat.run')
def run(strat_json):
    strat = Strategy('TEST')
    strat_dict = json.loads(strat_json)
    strat.load_from_dict(strat_dict)
    strat.run(viz=False)
    return "Completed!"
