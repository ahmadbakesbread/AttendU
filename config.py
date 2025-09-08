from configparser import ConfigParser
from urllib.parse import quote
from datetime import timedelta
import os

config = ConfigParser()
config.read('config.ini')
host = config['DATABASE']['host']
user = config['DATABASE']['username']
password = config['DATABASE']['password']
database = config['DATABASE']['db_name']
#driver = config['DATABASE']['driver']
port = config['DATABASE']['port']
password = quote(password, safe='')

def _csv(key, section='CORS'):
    return [x.strip() for x in config[section][key].split(',') if x.strip()]

CORS_ORIGIN = config['CORS']['origin']

class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    SECRET_KEY = config['FLASK']['secret_key']
    
    JWT_SECRET_KEY = config['AUTH']['jwt_secret']

    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(config['AUTH']['access_expires_minutes']))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(config['AUTH']['refresh_expires_days']))

    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'

    JWT_COOKIE_SECURE = False        # True on HTTPS
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = config['TEST']['secret_key']

    JWT_SECRET_KEY = config['AUTH']['jwt_secret']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'

    JWT_COOKIE_SECURE = False        # True on HTTPS
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False