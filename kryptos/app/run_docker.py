from flask.helpers import get_debug_flag
from kryptos.app.app import create_app
from kryptos.app.settings import DevConfig, DockerDevConfig, ProdConfig
from kryptos.platform.utils.outputs import in_docker


class ReverseProxied(object):

    def __init__(self, app, script_name=None, scheme=None, server=None):
        self.app = app
        self.script_name = script_name
        self.scheme = scheme
        self.server = server

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "") or self.script_name
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ["PATH_INFO"]
            if path_info.startswith(script_name):
                environ["PATH_INFO"] = path_info[len(script_name):]
        scheme = environ.get("HTTP_X_SCHEME", "") or self.scheme
        if scheme:
            environ["wsgi.url_scheme"] = scheme
        server = environ.get("HTTP_X_FORWARDED_SERVER", "") or self.server
        if server:
            environ["HTTP_HOST"] = server
        return self.app(environ, start_response)


if not in_docker():
    config = DevConfig

elif get_debug_flag():
    config = DockerDevConfig

else:
    config = ProdConfig

app = create_app(config)
app.wsgi_app = ReverseProxied(app.wsgi_app, script_name="/flask")
