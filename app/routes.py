import random
import time
from datetime import datetime

from flask import render_template, redirect
import requests
from app import app, login, db, turbo
from flask_login import login_required, current_user, login_user, logout_user

from app.forms import LoginForm
from app.models import User
from turbo_flask import Turbo
import threading


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/index")
@login_required
def index():
    cells_status = requests.get("http://roboprom.kvantorium33.ru/api/current").json()
    status = {
        "work": [0, []],
        "wait": [0, []],
        "error": [0, []],
        "off": [0, []]
    }
    mode = {
        "hand": [0, []],
        "auto": [0, []]
    }
    wait = {
        "no": [0, []],
        "wait": [0, []],
        "full_line": [0, []]
    }
    count = 0
    for cell in cells_status["data"]:
        # params = sorted(cell["params"], key=lambda a: a["timestamp"])
        cell_id = cell["cell"]
        for i in cell["params"]:
            p = i["param"]
            v = i["value"]
            if p == "status":
                if v == 0:
                    status["off"][0] += 1
                    status["off"][1].append(cell_id)
                if v == 1:
                    status["work"][0] += 1
                    status["work"][1].append(cell_id)
                if v == 2:
                    status["wait"][0] += 1
                    status["wait"][1].append(cell_id)
                if v == 3:
                    status["error"][0] += 1
                    status["error"][1].append(cell_id)
            if p == "wait":
                if v == 0:
                    wait["no"][0] += 1
                    wait["no"][1].append(cell_id)
                if v == 1:
                    wait["wait"][0] += 1
                    wait["wait"][1].append(cell_id)
                if v == 2:
                    wait["full_line"][0] += 1
                    wait["full_line"][1].append(cell_id)

            if p == "mode":
                if v == 0:
                    mode["hand"][0] += 1
                    mode["hand"][1].append(cell_id)
                if v == 1:
                    mode["auto"][0] += 1
                    mode["auto"][1].append(cell_id)

            if p == "count":
                count += 1
    production_data = {
        "speed": None,

        "all_speed": None,
        "bad": None,
    }
    # Скорость производства
    params = {
        "from": int(time.time()) - 60 * 60,
        "param": "count",
        "cell": 6
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

    if query["data"]:
        production_data["speed"] = 0
        for i in query["data"]:
            production_data["speed"] += i["value"]
    # Объём производства
    params = {
        "from": int(time.time()) - 60 * 60 * datetime.now().hour,
        "param": "count",
        "cell": 6
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()
    if query["data"]:
        production_data["all_speed"] = 0
        for i in query["data"]:
            production_data["all_speed"] += i["value"]
    # Объём брака (НЕДОДЕЛАНО)
    params = {
        "from": int(time.time()) - 60 * 60 * datetime.now().hour,
        "param": "count",
        "cell": 2
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

    if query["data"]:
        production_data["bad"] = 0
        for i in query["data"]:
            production_data["bad"] += i["value"]

    return render_template("index.html",
                           production_data=production_data,
                           status=status,
                           mode=mode,
                           wait=wait,
                           count=count,
                           cells=cells_status, r=random.randint(7, 9))


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me)
            return redirect("/")
        else:
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)
