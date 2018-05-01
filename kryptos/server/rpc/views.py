# -*- coding: utf-8 -*-

import json

from kryptos.platform.strategy import Strategy
from kryptos.server.extensions import jsonrpc

api = Blueprint('api', __name__)

@jsonrpc.method('Strat.run')
def run(strat_json):
    strat = Strategy('TEST')
    strat_dict = json.loads(strat_json)
    strat.load_from_dict(strat_dict)
    strat.run(viz=False)
 
    return 'Complete'

