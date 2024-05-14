import random
import time
from datetime import datetime, timedelta
from flask import jsonify, render_template, request, Blueprint
from flask_socketio import emit


class CostData:
    def __init__(self):
        self.cost1 = 3.3
        self.cost2 = 0.3
        self.cost3 = 0.9
        self.cost4 = 4
        self.climate_types = [
            "Företag 1 Kostnad",
            "Företag 1 Miljö",
            "Företag 2 Kostnad",
            "Företag 2 Miljö",
        ]
        self.cost_data_dict = {climate_type: [] for climate_type in self.climate_types}
        self.start_time = datetime.now()

    def generate_cost_data(self):
        time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        for climate_type in self.climate_types:
            if any(time_str == data[0] for data in self.cost_data_dict[climate_type]):
                return
        temp_cost1 = self.cost1 + random.uniform(-0.2, 0.2)
        temp_cost2 = self.cost2 + random.uniform(-0.26, 0.26)
        temp_cost3 = self.cost3 + random.uniform(-0.13, 0.13)
        temp_cost4 = self.cost4 + random.uniform(-0.13, 0.13)
        self.cost1 = temp_cost1 if temp_cost1 > 0 else self.cost1
        self.cost2 = temp_cost2 if temp_cost2 > 0 else self.cost2
        self.cost3 = temp_cost3 if temp_cost3 > 0 else self.cost3
        self.cost4 = temp_cost4 if temp_cost4 > 0 else self.cost4
        self.cost_data_dict["Företag 1 Kostnad"].append([time_str, self.cost1])
        self.cost_data_dict["Företag 1 Miljö"].append([time_str, self.cost2])
        self.cost_data_dict["Företag 2 Kostnad"].append([time_str, self.cost3])
        self.cost_data_dict["Företag 2 Miljö"].append([time_str, self.cost4])

    def get_mean_values(self):
        mean_values = {
            climate_type: round(
                sum([data[1] for data in self.cost_data_dict[climate_type]])
                / len(self.cost_data_dict[climate_type]),
                2,
            )
            for climate_type in self.climate_types
        }
        return mean_values

    def generate_cost(self, climate_type):
        self.generate_cost_data()
        climateValues = {
            "Företag 1 Kostnad": self.cost1,
            "Företag 1 Miljö": self.cost2,
            "Företag 2 Kostnad": self.cost3,
            "Företag 2 Miljö": self.cost4,
        }
        return climateValues[climate_type]

    def get_data_values(self, socketio):
        while True:
            try:
                self.start_time += timedelta(minutes=60)
                time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
                for climate_type in self.climate_types:
                    result = self.generate_cost(climate_type)
                    self.cost_data_dict[climate_type].append([time_str, result])
                    socketio.emit(
                        "cost_update",
                        {
                            "climate_type": climate_type,
                            "cost": result,
                            "time": time_str,
                        },
                    )
                for climate_type in self.climate_types:
                    if len(self.cost_data_dict[climate_type]) > 24:
                        self.cost_data_dict[climate_type].pop(0)
                time.sleep(5)
            except Exception as e:
                print(f"An error occurred in get_data_values: {e}")

    def send_cost_data(self, socketio):
        socketio.emit("cost_data", self.cost_data_dict)

    def setup_elpris_socketio(self, socketio):
        for _ in range(24):
            self.start_time += timedelta(minutes=60)
            self.generate_cost_data()
        socketio.start_background_task(self.get_data_values, socketio)
        socketio.start_background_task(self.send_cost_data, socketio)


elpris_bp = Blueprint("elpris", __name__)
cost_data = CostData()


@elpris_bp.route("/elpris")
def elpris():
    return render_template("elpris/elpris.html")


@elpris_bp.route("/cost_data", methods=["GET"])
def cost_data_route():
    lastDataPointTime = request.args.get("lastDataPointTime")
    if lastDataPointTime is not None:
        lastDataPointTime = datetime.strptime(lastDataPointTime, "%Y-%m-%d %H:%M:%S")
        for climate_type in cost_data.climate_types:
            cost_data.cost_data_dict[climate_type] = [
                data
                for data in cost_data.cost_data_dict[climate_type]
                if datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") > lastDataPointTime
            ]
    return jsonify(cost_data.cost_data_dict)


def setup_elpris_socketio(socketio):
    cost_data.setup_elpris_socketio(socketio)


# import random
# import time
# from datetime import datetime
# from flask import jsonify, render_template, request, Blueprint
# from flask_socketio import emit
# from datetime import timedelta, datetime


# elpris_bp = Blueprint("elpris", __name__)


# cost1 = 3.3
# cost2 = 0.3
# cost3 = 0.9
# cost4 = 4


# climate_types = [
#     "Företag 1 Kostnad",
#     "Företag 1 Miljö",
#     "Företag 2 Kostnad",
#     "Företag 2 Miljö",
# ]

# cost_data_dict = {climate_type: [] for climate_type in climate_types}

# # Initialize the start time to the current time
# start_time = datetime.now()


# @elpris_bp.route("/elpris")
# def elpris():
#     return render_template("elpris/elpris.html")


# @elpris_bp.route("/cost_data", methods=["GET"])
# def cost_data():
#     lastDataPointTime = request.args.get("lastDataPointTime")
#     if lastDataPointTime is not None:
#         lastDataPointTime = datetime.strptime(lastDataPointTime, "%Y-%m-%d %H:%M:%S")
#         for climate_type in climate_types:
#             cost_data_dict[climate_type] = [
#                 data
#                 for data in cost_data_dict[climate_type]
#                 if datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") > lastDataPointTime
#             ]
#     return jsonify(cost_data_dict)


# def setup_elpris_socketio(socketio):
#     global start_time, cost_data_dict, cost1, cost2, cost3, cost4, cost_data_dict

#     def generate_cost_data():
#         global cost1, cost2, cost3, cost4, start_time, cost_data_dict

#         # Update the time
#         time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

#         # Check if a data point with the same timestamp already exists for any company type
#         for climate_type in climate_types:
#             if any(time_str == data[0] for data in cost_data_dict[climate_type]):
#                 return

#         # Generate new cost values for each company type
#         temp_cost1 = cost1 + random.uniform(-0.2, 0.2)
#         temp_cost2 = cost2 + random.uniform(-0.26, 0.26)
#         temp_cost3 = cost3 + random.uniform(-0.13, 0.13)
#         temp_cost4 = cost4 + random.uniform(-0.13, 0.13)

#         cost1 = temp_cost1 if temp_cost1 > 0 else cost1
#         cost2 = temp_cost2 if temp_cost2 > 0 else cost2
#         cost3 = temp_cost3 if temp_cost3 > 0 else cost3
#         cost4 = temp_cost4 if temp_cost4 > 0 else cost4

#         # Update the cost data dict
#         cost_data_dict["Företag 1 Kostnad"].append([time_str, cost1])
#         cost_data_dict["Företag 1 Miljö"].append([time_str, cost2])
#         cost_data_dict["Företag 2 Kostnad"].append([time_str, cost3])
#         cost_data_dict["Företag 2 Miljö"].append([time_str, cost4])

#         # Calculate the mean values
#         mean_values = {
#             "Företag 1 Kostnad": round(
#                 sum([data[1] for data in cost_data_dict["Företag 1 Kostnad"]])
#                 / len(cost_data_dict["Företag 1 Kostnad"]),
#                 2,
#             ),
#             "Företag 1 Miljö": round(
#                 sum([data[1] for data in cost_data_dict["Företag 1 Miljö"]])
#                 / len(cost_data_dict["Företag 1 Miljö"]),
#                 2,
#             ),
#             "Företag 2 Kostnad": round(
#                 sum([data[1] for data in cost_data_dict["Företag 2 Kostnad"]])
#                 / len(cost_data_dict["Företag 2 Kostnad"]),
#                 2,
#             ),
#             "Företag 2 Miljö": round(
#                 sum([data[1] for data in cost_data_dict["Företag 2 Miljö"]])
#                 / len(cost_data_dict["Företag 2 Miljö"]),
#                 2,
#             ),
#         }

#         # Emit the updated mean values
#         socketio.emit("mean_update", mean_values)

#     # Generate the initial 24 values
#     print("Starting loop")
#     for _ in range(24):
#         start_time += timedelta(minutes=60)
#         print(_)
#         generate_cost_data()

#     def generate_cost(climate_type):
#         generate_cost_data()

#         climateValues = {
#             "Företag 1 Kostnad": cost1,
#             "Företag 1 Miljö": cost2,
#             "Företag 2 Kostnad": cost3,
#             "Företag 2 Miljö": cost4,
#         }
#         return climateValues[climate_type]

#     def get_data_values():
#         global start_time  # Add this line to access the global start_time variable
#         while True:
#             try:
#                 start_time += timedelta(
#                     minutes=60
#                 )  # Update the start_time variable once for each iteration
#                 time_str = start_time.strftime(
#                     "%Y-%m-%d %H:%M:%S"
#                 )  # Use the updated start_time variable
#                 for (
#                     climate_type
#                 ) in climate_types:  # runs this loop twice every 20 seconds
#                     result = generate_cost(climate_type)
#                     print(f"Adding {result} to {climate_type}")
#                     cost_data_dict[climate_type].append([time_str, result])
#                     print("Emitting cost_update")
#                     socketio.emit(
#                         "cost_update",
#                         {
#                             "climate_type": climate_type,
#                             "cost": result,
#                             "time": time_str,
#                         },
#                     )

#                 # Ensure the list does not grow indefinitely
#                 for climate_type in climate_types:
#                     if len(cost_data_dict[climate_type]) > 24:
#                         cost_data_dict[climate_type].pop(0)

#                 time.sleep(5)
#             except Exception as e:
#                 print(f"An error occurred in get_data_values: {e}")

#     @socketio.on("get_cost_data")
#     def send_cost_data():
#         emit("cost_data", cost_data_dict)

#     socketio.start_background_task(get_data_values)
#     socketio.start_background_task(send_cost_data)
