from flask import Flask
import requests
import urllib
import json
import datetime
import calendar
import pickle as pkl
import os

app = Flask(__name__)
app.config.from_object('config')

from app import views, models

if not app.debug: 
   import logging
   from logging.handlers import RotatingFileHandler
   file_handler = RotatingFileHandler('tmp/fly.log', 'a', 1 * 1024 * 1024, 10)
   file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
   app.logger.setLevel(logging.INFO)
   file_handler.setLevel(logging.INFO)
   app.logger.addHandler(file_handler)
   app.logger.info('fly startup')

