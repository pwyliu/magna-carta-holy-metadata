from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from mongokit import MongoClient
from .configure import conf_app, conf_logs, conf_sekrit

__VERSION__ = '0.0.2'

# App Config
app = Flask(__name__.split('.')[0], instance_relative_config=True)
conf_app(app)
conf_sekrit(app)

if not app.debug:
    conf_logs(app)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

#DB connection
db = MongoClient(app.config['MONGO_URI'])

import views
