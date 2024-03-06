from configparser import ConfigParser
from urllib.parse import quote
import os

config = ConfigParser()
config.read('config.ini')
host = config['DATABASE']['host']
user = config['DATABASE']['username']
password = config['DATABASE']['password']
database = config['DATABASE']['db_name']
driver = config['DATABASE']['driver']
port = config['DATABASE']['port']
password = quote(password, safe='')


class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    SECRET_KEY = config['FLASK']['secret_key']
    os.environ['FLASK_ENV'] = 'production'

class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = config['TEST']['secret_key']
    os.environ['FLASK_ENV'] = 'testing'