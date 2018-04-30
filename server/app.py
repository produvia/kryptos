# -*- coding: utf-8 -*-
"""The flask app module, containing the app factory function."""
from flask import Flask

from server import web, rpc
from server.extensions import jsonrpc
from server.settings import ProdConfig


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    app.logger.warn('Using {}'.format(config_object))
    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    """Register Flask extensions.

    Flask-Assistant does not need to be initalized here if declared as a blueprint.
    Other extensions such as flask-sqlalchemy and flask-migrate are reigstered here.
    If the entire flask app consists of only the Assistant, uncomment the code below.
    """
    jsonrpc.init_app(app)
    jsonrpc._register_browse(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints.

    When Flask-Assistant is used to create a blueprint within a standard flask app,
    it must be registered as such, rather that with init_app().

    If the entire flask app consists of only the Assistant, comment out the code below.
    """
    app.register_blueprint(web.views.blueprint)
    app.register_blueprint(rpc.views.api)
    return None
