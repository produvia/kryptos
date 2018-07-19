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

blueprint = Blueprint("public", __name__, url_prefix='/', static_folder='static/spa-mat')


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
def route_frontend(path):
    file_path = os.path.join(blueprint.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(blueprint.static_folder, 'index.html')
        return send_file(index_path)
