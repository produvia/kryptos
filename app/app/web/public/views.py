# -*- coding: utf-8 -*-
import os
from flask import Blueprint, render_template
from flask_user import current_user
import redis

# Grouping 2 blueprints together
blueprint = Blueprint('public', __name__, url_prefix='/')


@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)


redis_host = os.environ.get('REDISHOST', 'localhost')
redis_port = int(os.environ.get('REDISPORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port)


@blueprint.route('/testredis')
def index():
    value = redis_client.incr('counter', 1)
    return 'Visitor number: {}'.format(value)


@blueprint.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
