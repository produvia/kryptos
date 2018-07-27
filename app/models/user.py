import datetime

from app.extensions import db
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin


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


    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    @classmethod
    def create_from_strat(cls, strat_obj, user_id=None):

        instance = cls(id=strat_obj.id, name=strat_obj.name )

        d = strat_obj.to_dict()
        instance.trading_config = d['trading']
        instance.dataset_config = d['datasets']
        instance.indicators_config = d['indicators']
        instance.signals_config = d['signals']

        if user_id is not None:
            instance.user_id = user_id

        db.session.add(instance)
        db.session.commit()
