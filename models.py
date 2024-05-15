from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MatsvinnItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.String(200))
    warning_days = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)


class ElectricityCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    climate_type = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    cost = db.Column(db.Float, nullable=False)
