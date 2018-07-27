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
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MIGRATIONS_DIR = os.path.join(APP_DIR, 'models', 'migrations')

    # Flask-Assistant options
    CLIENT_ACCESS_TOKEN = os.getenv("CLIENT_ACCESS_TOKEN")
    DEV_ACCESS_TOKEN = os.getenv("DEV_ACCESS_TOKEN")
    ASSIST_ACTIONS_ON_GOOGLE = True
    REDIS_HOST = os.getenv('REDIS_HOST')
    RQ_POLL_INTERVAL = 1000

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'testkryptos123@gmail.com'
    MAIL_PASSWORD = 'lulxeqhsnlbnsjyd'
    MAIL_DEFAULT_SENDER = '"Kryptos AI" <noreply@example.com>'

    # Flask-User settings
    USER_APP_NAME = "Kryptos AI"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_ENABLE_CONFIRM_EMAIL = True
    USER_SEND_REGISTERED_EMAIL = True
    USER_AFTER_REGISTER_ENDPOINT = 'account.user_account'
    USER_AFTER_CONFIRM_ENDPOINT = 'account.user_account'
    USER_AFTER_LOGIN_ENDPOINT = 'account.user_account'
    USER_ENABLE_CONFIRM_EMAIL = False


class ProdConfig(Config):
    """Production configuration."""

    ENV = "prod"
    DEBUG = False
    FRONTEND_URL = "http://kryptos.produvia.com"
    API_URL = "http://web:5000/api"
    TELEGRAM_BOT = 'KryptosAIBot'


class DockerDevConfig(Config):
    ENV = "docker-dev"
    DEBUG = True
    BASE_URL = os.getenv('NGROK_URL', 'http://0.0.0.0:5000/')
    FRONTEND_URL = BASE_URL
    API_URL = "http://web:5000/api"
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_SEND_REGISTERED_EMAIL = False
    TELEGRAM_BOT = 'kryptos_dev_bot'


class DevConfig(Config):
    """Development configuration."""

    ENV = "dev"
    DEBUG = True
    BASE_URL = os.getenv('NGROK_URL', 'http://0.0.0.0:5000/')
    FRONTEND_URL = BASE_URL
    API_URL = os.path.join(BASE_URL, 'api')
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/kryptos'
    USER_ENABLE_CONFIRM_EMAIL = False
    TELEGRAM_BOT = 'kryptos_dev_bot'
    # SQLALCHEMY_ECHO = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/testkryptos'