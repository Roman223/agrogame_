from os.path import abspath, join
import json

with open(abspath(join("agro_game", "etc", "config.json"))) as config_file:
    config = json.load(config_file)


class Config:
    SECRET_KEY = config.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
