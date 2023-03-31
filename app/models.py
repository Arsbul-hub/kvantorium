from app import db, login
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return 'Пользователь {}'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CellsCause(UserMixin, db.Model):
    cell = db.Column(db.Integer, primary_key=True)
    cause = db.Column(db.String())
    timestamp = db.Column(db.Integer)
