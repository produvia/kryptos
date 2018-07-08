# -*- coding: utf-8 -*-
"""Application configuration.

See https://github.com/sloria/cookiecutter-flask for configuration options with other flask-extensions
"""
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.getenv("KRYPTOS_SECRET", "secret-key")  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))

    # Flask-Assistant options
    CLIENT_ACCESS_TOKEN = os.getenv("CLIENT_ACCESS_TOKEN")
    DEV_ACCESS_TOKEN = os.getenv("DEV_ACCESS_TOKEN")
    ASSIST_ACTIONS_ON_GOOGLE = True
    REDIS_HOST = os.getenv('REDIS_HOST')
    RQ_POLL_INTERVAL = 1000


class ProdConfig(Config):
    """Production configuration."""

    ENV = "prod"
    DEBUG = False
    API_URL = "http://35.233.156.192/api"


class DockerDevConfig(object):
    ENV = "docker-dev"
    DEBUG = True
    API_URL = "http://web:5000/api"


class DevConfig(Config):
    """Development configuration."""

    ENV = "dev"
    DEBUG = True
    API_URL = "http://127.0.0.1:5000/api"


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
