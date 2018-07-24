# -*- coding: utf-8 -*-
"""The flask app module, containing the app factory function."""
from flask import Flask, current_app
from flask.helpers import get_debug_flag
import logging

from flask_user import UserManager
import rq_dashboard

from app import web, api, bot, models
from app.extensions import jsonrpc, cors, db, migrate
from app.settings import DevConfig, DockerDevConfig, ProdConfig
from kryptos.utils.outputs import in_docker

logging.getLogger('flask_assistant').setLevel(logging.INFO)


def get_config():
    if not in_docker():
        config = DevConfig

    elif get_debug_flag():
        config = DockerDevConfig

    else:
        config = ProdConfig

    return config

def create_app(config_object=None):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    if config_object is None:
        config_object = get_config()

    app = Flask(__name__.split(".")[0])
    app.config.from_object(rq_dashboard.default_settings)
    app.config.from_object(config_object)
    app.logger.warn("Using {}".format(config_object))
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
    cors.init_app(app, resources={r"*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db, directory=app.config['MIGRATIONS_DIR'])

     # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, models.user.User)

    return None


def register_blueprints(app):
    """Register Flask blueprints.

    When Flask-Assistant is used to create a blueprint within a standard flask app,
    it must be registered as such, rather that with init_app().

    If the entire flask app consists of only the Assistant, comment out the code below.
    """
    app.register_blueprint(web.views.blueprint)
    app.register_blueprint(api.views.api)
    app.register_blueprint(bot.assistant.blueprint)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

    return None
