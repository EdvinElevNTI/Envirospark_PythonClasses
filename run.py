from factory import create_app
from models import db

socketio, app = create_app()

if __name__ == "__main__":
    db.init_app(app)
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", use_reloader=True, log_output=False)

# from factory import create_app

# socketio, app = create_app()
# if __name__ == '__main__':

#     socketio.run(app, host="0.0.0.0", use_reloader=True, log_output=False)
