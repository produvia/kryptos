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


    invoices = db.relationship("Strategy", backref="user", lazy=True)
    # User information
    # first_name = db.Column(db.String(100), nullable=False, server_default='')
    # last_name = db.Column(db.String(100), nullable=False, server_default='')


class Strategy(db.Model):
    id = db.Column(db.String(), nullable=False, unique=True, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=False)
    created_at = db.Column(db.DateTime())

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
