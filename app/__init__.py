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
cells_names = {
    1: "Выкладка фишек",
    2: "Сортировка",
    3: "Маркировка",
    4: "Выкладка оснований",
    5: "Раскладка",
    6: "Упаковка"
}
states_names = {
    "wait": {
        0: "Нет ожидания",
        1: "Ожидание заготовок на входе",
        2: "Линия переполнена или ожидание готовности следующей ячейки"
    },
    "status": {
        0: "Выключена",
        1: "Работает",
        2: "Ожидание",
        3: "Ошибка"
    }

}
from app import routes, models
