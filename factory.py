from flask import Flask, render_template
from blueprints import chart_bp, about_bp, elpris_bp, matsvinn_bp, setup_chart_socketio, setup_elpris_socketio
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.register_blueprint(about_bp)
    app.register_blueprint(elpris_bp)
    app.register_blueprint(matsvinn_bp)
    socketio = SocketIO(app)
    
    setup_chart_socketio(socketio)
    setup_elpris_socketio(socketio)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///song_library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'you-will-never-guess'

    db = SQLAlchemy(app)

    @app.route("/", methods=["GET"])
    def home():
        return render_template("base.html")


    return socketio, app