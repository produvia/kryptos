# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import os
import json
from flask import current_app, send_file, Blueprint, Response, render_template, flash, url_for, request, redirect, jsonify
import redis
from rq import Queue, Connection

from kryptos.strategy import Strategy
from kryptos.app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.worker import worker
from kryptos.app.web.forms import TradeInfoForm

blueprint = Blueprint("public", __name__, url_prefix='/', static_folder='../static/spa-mat')


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    # return render_template('index.html')

    if not in_docker():
        import requests
        return requests.get('http://localhost:8080/{}'.format(path)).text
    file_path = os.path.join(blueprint.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(blueprint.static_folder, 'index.html')
        return send_file(index_path)
