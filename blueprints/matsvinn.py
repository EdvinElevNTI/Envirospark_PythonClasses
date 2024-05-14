from flask import Flask, jsonify, render_template, request, redirect, url_for, Blueprint
import threading
import time
from datetime import datetime, timedelta
import subprocess
import json

# Initialize the Flask application.
matsvinn_bp = Blueprint('matsvinn', __name__)

class Data():
  def __init__(self):
    # Data and additional functions
    self.expiration_dict = {}
    self.warnings = []
    self.warning_days = 2
    self.data = 0
    self.nr = 1

    # Estimated procentual amount in bag of each category
    self.meat_p = 0.28
    self.harvest_p = 0.47
    self.veggies_p = 0.25

    # Average cost per kilo (kr)
    self.meat_c = 108
    self.harvest_c = 30
    self.veggies_c = 50

class HandleList():
  def __init__(self, data):
     self.data = data

  def expiration_checker(self): # Check for warnings in expiration_list every n seconds
    while True:
        self.warning_check(self.data.expiration_dict)
        time.sleep(self.data.warning_check_interval)

  def warning_check(self, expiration_dict):
      current_date = datetime.now()
    
      for key, item in expiration_dict.items():  # Iterate over key-value pairs

          difference = item.expiry_days()
          warning_days = int(item.warning_days)
          warning_days *= -1  # Convert to negative

          # If expired
          if difference.days > 0:
              item.expired = True
              item.warning = f"Expired: {item.name} expired on {item.expiration_date.strftime('%Y-%m-%d')} ({item.note})"

          # If about to expire
          elif 0 >= difference.days >= warning_days:
              item.expired = False
              item.warning = f"Warning: {item.name} expires soon on {item.expiration_date.strftime('%Y-%m-%d')} ({item.note})"

          # If no warning
          else:
              item.expired = False
              item.warning = None

class MatCalc():
  def __init__(self, data):
    self.data = data
  
  # Calculate estimated wasted money and round to whole number
  def calc_cost(self, bags, avg_weight):
    total_cost = bags * ((self.data.meat_c * self.data.meat_p) + (self.data.harvest_c * self.data.harvest_p) +
                        (self.data.veggies_c * self.data.veggies_p)) * avg_weight
    total_cost = round(total_cost)

    return total_cost

  # Decide the message
  def decide_message(self, bags, avg_weight):
    
    total_cost = self.calc_cost(bags, avg_weight)

    # <100
    if total_cost < 100:
      message = "Du slösar pengar (varje vecka/månad/etc.) som tillslut kan bli ett biobesök eller en mysig middag på en restaurang"

    # 100 - 200
    elif total_cost >= 100 and total_cost <= 200:
      message = "Det är ungefär kostnaden för en Netflix prenumeration och/eller Spotify Premium, eller ett besök på bio med vänner"
    
    # >200
    else:
      message = "Du slösar ungefär kostnaden för " + str(round(total_cost/109)) + " Netflix eller Spotify Premium prenumerationer, eller andra tjänster"

    return message

class List:
    def __init__(self, name, expiration_date, note, warning_days, type):
        self.name = name
        self.expiration_date = expiration_date
        self.note = note
        self.warning_days = warning_days
        self.type = type
        self.warning = None  # For potential warnings, starts empty
        self.expired = False  # For potential expired items, starts False

    # Function to calculate the number of days until expiration
    def expiry_days(self):
        item_date = self.expiration_date
        current_date = datetime.now()
        difference = current_date - item_date
        return difference


# Instances of classes
data = Data()
matcalc = MatCalc(data)
handlelist = HandleList(data)

# GET the routes for the application
@matsvinn_bp.route("/matsvinn")
def matsvinn():
  return render_template("matsvinn/matsvinn.html", expiration_dict=data.expiration_dict, warnings=data.warnings)

# POST requests
@matsvinn_bp.route("/matsvinn_calc_post", methods=["POST"])
def calc_post():
  data = request.json
  bags = int(data['number'])  # Convert to int and into bags variable
  avg_weight = float(data['avg_weight'])

  result = str(matcalc.calc_cost(bags, avg_weight)) + " kr"
  message = matcalc.decide_message(bags, avg_weight)

  return jsonify(result=result, message=message)


@matsvinn_bp.route('/get_item/<int:key>')
def get_item(key):
    item = data.expiration_dict.get(key)
    if item is not None:
        return jsonify({
            'name': item.name,
            'expiration_date': item.expiration_date,
            'note': item.note,
            'warning_days': item.warning_days,
            'warning' : item.warning,
            'type': item.type,
            'expired': item.expired
        })
    else:
        return jsonify({'error': 'Invalid key'}), 400

@matsvinn_bp.route('/matsvinn_exp_add_item', methods=['POST'])
def add_item():

  name = request.form['name']
  expiration_date = datetime.strptime(request.form['expiration_date'], '%Y-%m-%d')
  note = request.form['note']
  warning_days = int(request.form['warning_days'])
  type = request.form['type']

  new_item = List(name, expiration_date, note, warning_days, type)
  data.expiration_dict[data.nr] = new_item
  handlelist.warning_check(data.expiration_dict)
  data.nr += 1
  
  return redirect(url_for('matsvinn.matsvinn'))

# Delete item
@matsvinn_bp.route('/delete_item', methods=['POST'])
def delete_item():
    index = int(request.form.get('index', -1))

    # Delete if valid index
    if index != -1 and index in data.expiration_dict:
        del data.expiration_dict[index]
        return redirect(url_for('matsvinn.matsvinn'))  # Redirect to the matsvinn route
    
    # Return error otherwise
    else:
        return jsonify({'error': 'Invalid index'}), 400

# Edit item
@matsvinn_bp.route('/edit_item', methods=['POST'])
def edit_item():
    index = int(request.form.get('index', -1)) # Set index to -1 if its empty to handle error
    new_name = request.form.get('new_name')
    new_expiration_date = request.form.get('new_expiration_date')
    new_note = request.form.get('new_note')
    new_warning_days = request.form.get('new_warning_days')
    new_type = request.form['new_type']

    # Check if valid index
    if index != -1 and index in data.expiration_dict:

        new_expiration_date = datetime.strptime(request.form.get('new_expiration_date'), '%Y-%m-%d')
            
        # Update items in expiration_dict
        data.expiration_dict[index].name = new_name
        data.expiration_dict[index].expiration_date = new_expiration_date
        data.expiration_dict[index].note = new_note
        data.expiration_dict[index].warning_days = new_warning_days
        data.expiration_dict[index].type = new_type
        data.warning_check(data.expiration_dict) # Check for warnings
        
        return redirect(url_for('matsvinn.matsvinn'))  # Redirect to the matsvinn route after editing
    
    # Return error otherwise
    else:
        return jsonify({'error': 'Invalid index'}), 400


# Assuming expiration_dict is a dictionary of objects of some class
serialized_expiration_dict = json.dumps({k: v.__dict__ for k, v in data.expiration_dict.items()})