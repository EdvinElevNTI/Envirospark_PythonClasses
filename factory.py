from flask import Flask, render_template
from blueprints import about_bp, elpris_bp, matsvinn_bp, setup_elpris_socketio
from flask_socketio import SocketIO
from models import db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.register_blueprint(about_bp)
    app.register_blueprint(elpris_bp)
    app.register_blueprint(matsvinn_bp)
    socketio = SocketIO(app)

    setup_elpris_socketio(socketio)

    @app.route("/", methods=["GET"])
    def home():
        return render_template("base.html")

    return socketio, app
