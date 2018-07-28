import datetime
import json
import uuid
from flask import current_app
from flask_user import UserMixin, current_user

from app.extensions import db



class User(db.Model, UserMixin):
    __tablename__ = 'users'

    # User auth keys are not stored in the db
    # Because catalyst utilzies auth files in the .catalyst directory
    # We can simply create auth files with the user ID and pass the file to the strategy

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')


    # User Authentication fields
    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False)

    telegram_id = db.Column(db.Integer, nullable=True, unique=True)
    telegram_username = db.Column(db.String(255), nullable=True, unique=True)
    telegram_photo = db.Column(db.String(), nullable=True, unique=False)
    telegram_auth_date = db.Column(db.Integer, nullable=True, unique=False)


    strategies = db.relationship("StrategyModel", backref="user", lazy=True)
    # User information
    # first_name = db.Column(db.String(100), nullable=False, server_default='')
    # last_name = db.Column(db.String(100), nullable=False, server_default='')

    def unlink_telegram(self):
        self.telegram_id = None
        self.telegram_username = None
        self.telegram_photo = None
        self.telegram_auth_date = None
        db.session.add(self)
        db.session.commit()


class StrategyModel(db.Model):
    __tablename__ = 'strategies'

    id = db.Column(db.String(), nullable=False, unique=True, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=False)
    created_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    trading_config = db.Column(db.JSON(), nullable=False, unique=False)
    dataset_config = db.Column(db.JSON(), nullable=False, unique=False)
    indicators_config = db.Column(db.JSON(), nullable=False, unique=False)
    signals_config = db.Column(db.JSON(), nullable=False, unique=False)


    status = db.Column(db.String(), nullable=True, unique=False, primary_key=False)

    result_json = db.Column(db.JSON(), nullable=True, unique=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    @classmethod
    def from_json(cls, strat_json, user_id=None):
        d = json.loads(strat_json)
        instance = cls()

        instance.id = d.get('id', str(uuid.uuid1()))
        instance.name = d.get('name')
        instance.trading_config = d.get('trading')
        instance.dataset_config = d.get('datasets')
        instance.indicators_config = d.get('indicators')
        instance.signals_config = d.get('signals')

        if user_id is not None:
            instance.user_id = user_id

        return instance

    def update_from_job(self, job):
        self.status = job.status
        current_app.logger.debug(f"Updating strategy {self.id} status: {self.status}")
        if job.result:
            current_app.logger.debug(f"Strategy {self.id} job has finished")
            self.result_json = job.result

        db.session.commit()

    def config_to_json(self):
        d = {
            'id': self.id,
            'name': self.name,
            'trading': self.trading_config,
            'datasets': self.dataset_config,
            'indicator': self.indicators_config,
            'signals_config': self.signals_config
        }
        return json.dumps(d)

    def pretty_result(self):
        string = ''
        if self.result_json is None:
            return None
        result_dict = json.loads(self.result_json)
        for k, v in result_dict.items():
            # nested dict with trading type as key
            metric, val = k, v["Backtest"]
            string += f"{metric}: {val}\n"
        return string
