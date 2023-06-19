from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import mysqldb
from Models import Base, Teacher
import bcrypt
from configparser import ConfigParser
from sqlalchemy.dialects.mysql import pymysql
from urllib.parse import quote

app = Flask(__name__)

config = ConfigParser()
config.read('config.ini')

host = config['DATABASE']['host']
user = config['DATABASE']['username']
password = config['DATABASE']['password']
database = config['DATABASE']['db_name']
driver = config['DATABASE']['driver']
port = config['DATABASE']['port']

password = quote(password, safe='')

# Create the SQLAlchemy engine
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base.metadata.create_all(bind=engine)
# Use this to create all the tables and information. 
# Only need to run this once!


if __name__ == '__main__':
    app.run(debug=True)
