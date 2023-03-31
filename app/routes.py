import random
import time
from datetime import datetime

import requests
from flask import render_template, redirect, request
from flask_login import login_required, current_user, login_user, logout_user

from app import app, login, cells_names, states_names, db
from app.forms import LoginForm
from app.models import User, CellsCause


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/index")
@login_required
def index():
    cells = requests.get("http://roboprom.kvantorium33.ru/api/current").json()["data"]

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
    for hour in range(datetime.now().hour):
        p = {
            "from": int(int(time.time()) - datetime.now().hour * 3600) + hour * 3600,
            "to": int(int(time.time()) - datetime.now().hour * 3600) + hour * 2 * 3600,
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

    table_data = []
    for c in cells:
        table_cell = {"index": c["cell"],
                      "status": states_names["status"][c["status"]],
                      "wait": states_names["wait"][c["wait"]],
                      "speed_hour": c["count_h"],
                      "speed_day": c["count_d"],
                      "work_hour": round(c["load_h"][1] * 100, 2),
                      "work_day": round(c["load_d"][1] * 100, 2)}
        table_data.append(table_cell)

    return render_template("index.html",
                           len=len,
                           cells_names=cells_names,
                           graph=graph,
                           table_data=table_data,
                           work_procent=0,
                           production_data=production_data,
                           count=count,
                           cells=cells, r=random.randint(7, 9))


@app.route("/Информация о ячейке")
def cell_info():
    # за текущий день
    cell_index = request.args.get("index")
    cell = requests.get("http://roboprom.kvantorium33.ru/api/current", params={"cell": cell_index}).json()["data"][0]

    cell_data = {
        "index": cell_index,
        "name": cells_names[int(cell_index)],
        "speed_hour": cell["count_h"],
        "speed_day": cell["count_d"],
        "work_hour": round(cell["load_h"][1] * 100, 2),
        "work_day": round(cell["load_d"][1] * 100, 2),
        "wait": cell["wait_d"],
        "states": cell["status_d"]
    }

    graph = []
    for hour in range(datetime.now().hour):
        p = {
            "from": int(int(time.time()) - datetime.now().hour * 3600) + hour * 3600,
            "to": int(int(time.time()) - datetime.now().hour * 3600) + hour * 2 * 3600,
            "cell": cell_index,
            "param": "status"
        }

        query = requests.get("http://roboprom.kvantorium33.ru/api/history", params=p).json()["data"]
        a = 0
        for i in query:
            a += i["value"]
        if query:
            graph.append(round(a / len(query)))
        else:
            graph.append(a)
    table_data1 = []
    for s in range(4):
        table_data1.append(
            {"status": states_names["status"][s],
             "time_day": cell["status_d"][s],
             "time_day_procent": int(round(cell["status_d"][s] / (3600 * 24), 2) * 100),
             "time_hour": cell["status_h"][s],
             "time_hour_procent": int(round(cell["status_h"][s] / 3600, 2) * 100),
             }
        )
    table_data2 = []
    for s in range(3):
        table_data2.append(
            {"wait": states_names["wait"][s],
             "time_day": cell["wait_d"][s],
             "time_day_procent": int(round(cell["wait_d"][s] / (3600 * 24), 2) * 100),
             "time_hour": cell["wait_h"][s],
             "time_hour_procent": int(round(cell["wait_h"][s] / 3600, 2) * 100),
             }
        )
    table_data3 = []
    for s in CellsCause.query.all():
        table_data3.append(
            {"cell": s.cell,
             "cause": s.cause,
             "time_sum": cell["wait_d"][s],
             "time_procent": s.timestamp,
             }
        )
    return render_template("Информация о ячейке.html", len=len, cell=cell_data, graph=graph, table_data1=table_data1,
                           table_data2=table_data2)


@app.route("/Онлайн монитор")
def monitor():
    cells = requests.get("http://roboprom.kvantorium33.ru/api/current").json()["data"]
    colors = [
        "lightgray",
        "lightgreen",
        "lightyellow",
        "lightred"
    ]
    return render_template("Онлайн монитор.html", cells=cells, colors=colors, round=round, int=int)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/Панель оператора", methods=["GET", "POST"])
def op_panel():
    cells = requests.get("http://roboprom.kvantorium33.ru/api/current")
    if cells.status_code == 504:
        return render_template("errors/502.html")

    colors = [
        "lightgray",
        "lightgreen",
        "lightyellow",
        "lightred"
    ]
    cause = request.args.get("cause")
    if cause:
        new_cell_cause = CellsCause(cell=request.args.get("cell"), cause=cause)
        db.session.add(new_cell_cause)
        db.session.commit()
    for cell in cells.json()["data"]:
        if cell["status"] != 0:
            CellsCause.query.filter_by(cell=cell["cell"]).delete()
            db.session.commit()
    return render_template("Панель оператора.html", cell=request.args.get("cell"), states_names=states_names,
                           cells=cells.json()["data"], cells_names=cells_names, colors=colors, round=round, int=int)


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
