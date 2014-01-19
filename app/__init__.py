import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir

#From microblog
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

#From 3BAM
application = app
UPLOAD_FOLDER = os.getcwd()
ALLOWED_EXTENSIONS = set(['txt'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER#configuring file to save data
app.secret_key = 'HappyHalloween'

from app import views, models