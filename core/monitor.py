import logging
from flask import Flask
import redis

from kryptos.settings import REDIS_HOST, REDIS_PORT


app = Flask(__name__)

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)


@app.route('/')
def index():
    logging.warn('Testing redis connection {}:{}'.format)
    value = redis_client.incr('counter', 1)
    return 'Visitor number: {}'.format(value), 200


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
