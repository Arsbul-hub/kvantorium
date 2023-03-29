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
    cells_names = {
        1: "Выкладка фишек",
        2: "Сортировка",
        3: "Маркировка",
        4: "Выкладка оснований",
        5: "Раскладка",
        6: "Упаковка"
    }
    cells_status = requests.get("http://roboprom.kvantorium33.ru/api/current").json()

    work_procent = []
    for table_cell in cells_status["data"]:
        for param in table_cell["params"]:
            if param["param"] == "status" and param["value"] == 1:
                w = int(time.time()) - param["timestamp"]
                work_procent.append((w / 3600) * 100)
    if work_procent:
        work_procent = sum(work_procent) / len(work_procent)
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
        "from": int(time.time()) - 10,  # за 10 секунд
        "param": "count",
        "cell": 6
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

    if query["data"]:
        production_data["speed"] = 0
        for i in query["data"]:
            production_data["speed"] += i["value"]
        production_data["speed"] *= 6 * 60  # превращаем в деталей в час
    # Объём производства
    params = {
        "from": int(time.time()) - 60 * 60 * datetime.now().hour,
        "param": "count",
        "cell": 6
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()
    print(query)
    if query["data"]:
        production_data["all_speed"] = 0
        for i in query["data"]:
            production_data["all_speed"] += i["value"]
    # Процент брака

    params = {
        "from": int(time.time()) - 60 * 60 * datetime.now().hour,
        "param": "count",
        "cell": 2
    }
    query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()
    all_input_query = requests.get("http://roboprom.kvantorium33.ru/api/current", params={"cell": 1}).json()["data"][0][
        "params"]
    all_input = 1
    for p in all_input_query:
        if p["param"] == "count":
            all_input = p["value"]

    if query["data"]:
        production_data["bad"] = 0
        bad = 0
        for i in range(len(query["data"])):
            if i < len(query["data"]) - 1 and query["data"][i + 1] == 0:
                bad = query["data"][i]["value"]

            else:
                bad = query["data"][i]["value"]

        production_data["bad"] = int(round(bad / all_input, 2) * 100)
    # Граффик
    graph = []
    for hour in range(24):
        params = {
            "from": int(time.time()) - datetime.now().hour * 60 * 60,

            "param": "count",
            "cell": 6
        }
        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

        h = 0
        for i in query["data"]:
            if i["param"] == "count":
                h += i["value"]
        graph.append(h)
    # таблица
    table_data = []

    query = requests.get("http://roboprom.kvantorium33.ru/api/current").json()

    k = {
        "wait": {
            0: "Нет ожидания",
            1: "Ожидание заготовок на входе",
            2: "линия переполнена или ожидание готовности следующей ячейки"
        },
        "status": {
            0: "выключена",
            1: "работает",
            2: "ожидание",
            3: "ошибка"
        }

    }
    for cells in query["data"]:
        table_cell = {"index": cells["cell"],
                      "status": "",
                      "wait": "",
                      "speed_hour": 0,
                      "speed_day": 0,
                      "work_hour": 0,
                      "work_day": 0}
        cell_params = cells["params"]
        for param in cell_params:
            if param["param"] == "status":
                table_cell["status"] = k["status"].get(param["value"])
            if param["param"] == "wait":
                table_cell["wait"] = k["wait"].get(param["value"])

        ## количество обработанных заготовок за последний час ##

        params = {
            "from": int(time.time()) - 60 * 60,
            "cell": cells["cell"],
            "param": "count"
        }
        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

        for i in range(len(query["data"])):
            if i < len(query["data"]) - 1 and query["data"][i + 1] == 0:
                table_cell["speed_hour"] = query["data"][i]["value"]

            else:
                table_cell["speed_hour"] = query["data"][i]["value"]

        ## количество обработанных заготовок за текущий день ##

        params = {
            "from": int(time.time()) - datetime.now().hour * 60 * 60,
            "cell": cells["cell"],
            "param": "count"
        }
        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

        for i in range(len(query["data"])):
            if i < len(query["data"]) - 1 and query["data"][i + 1] == 0:
                table_cell["speed_day"] += query["data"][i]["value"]

            else:
                table_cell["speed_day"] = query["data"][i]["value"]

        ## загрузка оборудования за последний час ##
        params = {
            "timestamp": int(time.time()) - 60 * 60,
            "cell": cells["cell"],
            "param": "status"
        }
        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=params).json()

        for i in range(len(query["data"])):
            param = query["data"][i]

            if param["param"] == "status" and param["value"] == 1 and i < len(query["data"]) - 1 and \
                    query["data"][i + 1]["value"] == 0:
                print(int(time.time()) - param["ts"])
                table_cell["work_hour"] = int(time.time()) - int(
                    round((int(time.time()) - param["ts"]) / 3600, 2) * 100)

            else:
                print(param)
                table_cell["work_hour"] = int(time.time()) - int(
                    round((int(time.time()) - param["ts"]) / 3600, 2) * 100)
        table_data.append(table_cell)

    return render_template("index.html",
                           cells_names=cells_names,
                           table_data=table_data,
                           graph=graph,
                           work_procent=work_procent,
                           production_data=production_data,
                           status=status,
                           mode=mode,
                           wait=wait,
                           count=count,
                           cells=cells_status, r=random.randint(7, 9))


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
