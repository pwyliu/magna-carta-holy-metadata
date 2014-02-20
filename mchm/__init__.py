import logging
import os
from logging import Formatter
from logging.handlers import RotatingFileHandler
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from mongokit import MongoClient
import site_config


#DB connection
db = MongoClient(site_config.MONGO_URI)

#App Config
app = Flask(__name__)
app.debug = site_config.APP_DEBUG_MODE
app.wsgi_app = ProxyFix(app.wsgi_app)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

#File Logger Config
if not os.path.exists(site_config.LOG_PATH):
    open(site_config.LOG_PATH, 'w+').close()

file_handler = RotatingFileHandler(site_config.LOG_PATH,
                                   mode='a',
                                   maxBytes=site_config.LOG_SIZE,
                                   backupCount=site_config.LOG_ARCHIVES)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(Formatter(site_config.LOG_FORMAT))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

#start up
app.logger.info('{!s} started.'.format(site_config.APP_NAME))
import views
