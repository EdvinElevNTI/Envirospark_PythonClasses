from flask import Flask, jsonify, render_template, request, redirect, url_for, Blueprint
import threading
import time
from datetime import datetime, timedelta
import subprocess
import json
from models import MatsvinnItem, db

matsvinn_bp = Blueprint("matsvinn", __name__)


class ExpirationList:
    def __init__(self):
        self.items = {}
        self.nr = 1

    def add_item(self, item):
        self.items[self.nr] = item
        self.nr += 1

    def delete_item(self, index):
        if index in self.items:
            del self.items[index]

    def edit_item(
        self, index, new_name, new_expiration_date, new_note, new_warning_days, new_type
    ):
        if index in self.items:
            self.items[index].name = new_name
            self.items[index].expiration_date = new_expiration_date
            self.items[index].note = new_note
            self.items[index].warning_days = new_warning_days
            self.items[index].type = new_type

    def to_json(self):
        return json.dumps([item.__dict__ for item in self.items.values()])


class ListItem:
    def __init__(self, name, expiration_date, note, warning_days, type):
        self.name = name
        self.expiration_date = expiration_date
        self.note = note
        self.warning_days = warning_days
        self.type = type
        self.warning = None
        self.expired = False

    def expiry_days(self):
        current_date = datetime.now()
        difference = self.expiration_date - current_date
        return difference


class MatCalc:
    def __init__(self):
        self.meat_p = 0.28
        self.harvest_p = 0.47
        self.veggies_p = 0.25
        self.meat_c = 108
        self.harvest_c = 30
        self.veggies_c = 50

    def calc_cost(self, bags, avg_weight):
        total_cost = (
            bags
            * (
                (self.meat_c * self.meat_p)
                + (self.harvest_c * self.harvest_p)
                + (self.veggies_c * self.veggies_p)
            )
            * avg_weight
        )
        return round(total_cost)

    def decide_message(self, bags, avg_weight):
        total_cost = self.calc_cost(bags, avg_weight)
        if total_cost < 100:
            message = "You are wasting money which could be used for entertainment."
        elif 100 <= total_cost <= 200:
            message = "It's approximately the cost of a Netflix or Spotify subscription, or a movie night out."
        else:
            message = f"You are wasting money equivalent to {round(total_cost/109)} Netflix or Spotify subscriptions."
        return message


expiration_list = ExpirationList()
mat_calc = MatCalc()


@matsvinn_bp.route("/matsvinn")
def matsvinn():
    items = MatsvinnItem.query.all()
    return render_template("matsvinn/matsvinn.html", expiration_dict=items, warnings=[])


@matsvinn_bp.route("/matsvinn_calc_post", methods=["POST"])
def calc_post():
    data = request.json
    bags = int(data["number"])
    avg_weight = float(data["avg_weight"])

    result = str(mat_calc.calc_cost(bags, avg_weight)) + " kr"
    message = mat_calc.decide_message(bags, avg_weight)

    return jsonify(result=result, message=message)


@matsvinn_bp.route("/get_item/<int:key>")
def get_item(key):
    item = expiration_list.items.get(key)
    if item:
        return jsonify(
            {
                "name": item.name,
                "expiration_date": item.expiration_date.strftime("%Y-%m-%d"),
                "note": item.note,
                "warning_days": item.warning_days,
                "warning": item.warning,
                "type": item.type,
                "expired": item.expired,
            }
        )
    else:
        return jsonify({"error": "Invalid key"}), 400


@matsvinn_bp.route("/matsvinn_exp_add_item", methods=["POST"])
def add_item():
    name = request.form["name"]
    expiration_date = request.form["expiration_date"]
    note = request.form["note"]
    warning_days = int(request.form["warning_days"])
    type = request.form["type"]

    new_item = MatsvinnItem(
        name=name,
        expiration_date=expiration_date,
        note=note,
        warning_days=warning_days,
        type=type,
    )
    db.session.add(new_item)
    db.session.commit()

    return redirect(url_for("matsvinn"))


@matsvinn_bp.route("/delete_item", methods=["POST"])
def delete_item():
    index = int(request.form.get("index", -1))
    expiration_list.delete_item(index)
    return redirect(url_for("matsvinn"))


@matsvinn_bp.route("/edit_item", methods=["POST"])
def edit_item():
    index = int(request.form.get("index", -1))
    new_name = request.form.get("new_name")
    new_expiration_date = datetime.strptime(
        request.form.get("new_expiration_date"), "%Y-%m-%d"
    )
    new_note = request.form.get("new_note")
    new_warning_days = request.form.get("new_warning_days")
    new_type = request.form.get("new_type")

    expiration_list.edit_item(
        index, new_name, new_expiration_date, new_note, new_warning_days, new_type
    )
    return redirect(url_for("matsvinn"))
