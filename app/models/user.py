from app.extensions import db
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    # User auth keys are not stored in the db
    # Because catalyst utilzies auth files in the .catalyst directory
    # We can simply create auth files with the user ID and pass the file to the strategy

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
