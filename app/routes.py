import random
import time
from datetime import datetime
from pprint import pprint

from flask import render_template, redirect, request
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
    cells = requests.get("http://roboprom.kvantorium33.ru/api/current").json()["data"]
    cells_names = {
        1: "Выкладка фишек",
        2: "Сортировка",
        3: "Маркировка",
        4: "Выкладка оснований",
        5: "Раскладка",
        6: "Упаковка"
    }
    production_data = {
        "speed": None,
        "all_speed": None,
        "bad": None,
        "work_procent": 0,
        "status": {
            "work": [0, []],
            "wait": [0, []],
            "error": [0, []],
            "off": [0, []]
        },
        "mode": {
            "hand": [0, []],
            "auto": [0, []]
        },
        "wait": {
            "no": [0, []],
            "wait": [0, []],
            "full_line": [0, []]
        }
    }
    count = 0
    for cell in cells:
        # params = sorted(cell["params"], key=lambda a: a["timestamp"])
        cell_id = cell["cell"]
        for i in cell["params"]:
            p = i["param"]
            v = i["value"]
            if p == "status":
                if v == 0:
                    production_data["status"]["off"][0] += 1
                    production_data["status"]["off"][1].append(cell_id)
                if v == 1:
                    production_data["status"]["work"][0] += 1
                    production_data["status"]["work"][1].append(cell_id)
                if v == 2:
                    production_data["status"]["wait"][0] += 1
                    production_data["status"]["wait"][1].append(cell_id)
                if v == 3:
                    production_data["status"]["error"][0] += 1
                    production_data["status"]["error"][1].append(cell_id)
            if p == "wait":
                if v == 0:
                    production_data["wait"]["no"][0] += 1
                    production_data["wait"]["no"][1].append(cell_id)
                if v == 1:
                    production_data["wait"]["wait"][0] += 1
                    production_data["wait"]["wait"][1].append(cell_id)
                if v == 2:
                    production_data["wait"]["full_line"][0] += 1
                    production_data["wait"]["full_line"][1].append(cell_id)

            if p == "mode":
                if v == 0:
                    production_data["mode"]["hand"][0] += 1
                    production_data["mode"]["hand"][1].append(cell_id)
                if v == 1:
                    production_data["mode"]["auto"][0] += 1
                    production_data["mode"]["auto"][1].append(cell_id)

            if p == "count":
                count += 1

    # Скорость
    if cells[5]["count_h"]:
        production_data["speed"] = cells[5]["count_h"]

    # Объём производства
    if cells[5]["count_d"]:
        production_data["all_speed"] = cells[5]["count_d"]

    # Процент брака
    if cells[5]["count_d"]:

        production_data["bad"] = int(round(cells[1]["count_d"] / cells[0]["count_d"], 2) * 100)

    # Средняя загрузка

    for c in cells:
        production_data["work_procent"] += c["load_h"][1]

    production_data["work_procent"] = int(round(production_data["work_procent"] / 6, 2) * 100)

    # таблица
    graph = []
    for hour in range(24):
        p = {
            "timestamp": int(int(time.time()) - datetime.now().hour * 3600) + hour,
            "cell": 6,
            "param": "count"
        }
        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=p).json()["data"]
        a = 0
        for i in range(len(query)):
            d = query[i]
            if i < len(query) - 1 and query[i + 1] == 0 and d != 0:
                a += d["value"]
            elif i == len(query) - 1:
                a += d["value"]
        graph.append(a)

    k = {
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
    table_data = []
    for c in cells:
        table_cell = {"index": c["cell"],
                      "status": k["status"][c["status"]],
                      "wait": k["wait"][c["wait"]],
                      "speed_hour": c["count_h"],
                      "speed_day": c["count_d"],
                      "work_hour": round(c["load_h"][1] * 100, 2),
                      "work_day": round(c["load_d"][1] * 100, 2)}
        table_data.append(table_cell)


    return render_template("index.html",
                           cells_names=cells_names,
                           graph=graph,
                           table_data=table_data,
                           work_procent=0,
                           production_data=production_data,
                           count=count,
                           cells=cells, r=random.randint(7, 9))


@app.route("/Информация о ячейке")
def cell_info():
    cell_index = request.args.get("cell")
    return render_template("Информация о ячейке.html")


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
