from agro_game import db
from flask_login import UserMixin
from agro_game import login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, registration_date):
        self.username = username
        self.registration_date = registration_date


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    session_start = db.Column(db.DateTime, nullable=False)
    session_time = db.Column(db.DateTime, nullable=False)
    session_finish = db.Column(db.DateTime, nullable=False, default=None)
    money = db.Column(db.Float, nullable=True)
    productivity = db.Column(db.Float, nullable=True, default=0)


class Cultures(db.Model):
    __tablename__ = 'cultures'
    id = db.Column(db.Integer, primary_key=True)
    culture_name = db.Column(db.Text)


class Fields(db.Model):
    __tablename__ = 'users_fields'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    f_type = None
    area = db.Column(db.Float, nullable=False)
    prev_culture = db.Column(db.Text)
    productivity = db.Column(db.Float)
    temp_soil = db.Column(db.Float)
    temp_air = db.Column(db.Float)
    pH = db.Column(db.Float)
    price = db.Column(db.Float)
    humidity = db.Column(db.Float)
    watercapacity = db.Column(db.Float)
    N = db.Column(db.Float)
    P = db.Column(db.Float)
    K = db.Column(db.Float)