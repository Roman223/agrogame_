from flask import Flask
from typing import Callable
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from agro_game.config import Config


class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    DateTime: Callable
    Text: Callable
    relationship: Callable
    ForeignKey: Callable


app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = MySQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

try:
    from agro_game import routes
except:
    pass
