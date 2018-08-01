# -*- coding: utf-8 -*-
import os
from flask import Blueprint, render_template
from flask_user import current_user, current_app
import redis
import logging
# Grouping 2 blueprints together
blueprint = Blueprint('public', __name__, url_prefix='/')


REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDI_PORT = int(os.environ.get('REDIS_PORT', 6379))
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDI_PORT)

@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)


@blueprint.route('/testredis')
def index():
    current_app.logger.warn(f'Testing Redis Conenction: {REDIS_HOST}:{REDI_PORT}')
    value = redis_client.incr('counter', 1)
    return 'Visitor number: {}'.format(value)


@blueprint.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
