# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_jsonrpc import JSONRPC
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


jsonrpc = JSONRPC(service_url="/api", enable_web_browsable_api=True)
cors = CORS()
db = SQLAlchemy()
migrate = Migrate()
