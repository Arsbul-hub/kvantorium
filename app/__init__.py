import locale

import pymorphy2 as pymorphy2
from flask import Flask
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from turbo_flask import Turbo
from livereload import Server
from config import Config

app = Flask(__name__)
server = Server(app.wsgi_app)
app.config.from_object(Config)

ckeditor = CKEditor(app)
turbo = Turbo(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)
login = LoginManager(app)
login.login_view = 'login'

morph = pymorphy2.MorphAnalyzer()
locale.setlocale(
    category=locale.LC_ALL,
    locale="Russian"
)
from app import routes, models
