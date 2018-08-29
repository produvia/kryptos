import logging
import os

from flask import Flask
import redis

app = Flask(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis-19779.c1.us-central1-2.gce.cloud.redislabs.com')
REDIS_PORT = os.getenv('REDIS_PORT', 19779)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) or get_from_datastore('REDIS_PASSWORD', 'production')

CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)



@app.route('/')
def index():
    logging.warn('Testing redis connection {}:{}'.format)
    value = redis_client.incr('counter', 1)
    return 'Visitor number: {}'.format(value)


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
