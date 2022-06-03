from flask_login import UserMixin

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    is_admin = db.Column(db.Boolean())


class MonthlyMeasurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    location = db.Column(db.Integer, db.ForeignKey('location.id'))
    average_temp = db.Column(db.Float)
    days_with_snow_coverage = db.Column(db.Integer)
    average_snow_coverage = db.Column(db.Float)
    average_snow_coverage_only_available = db.Column(db.Float)
    sunshine_hours = db.Column(db.Float)
    average_max_temp = db.Column(db.Float)
    average_min_temp = db.Column(db.Float)
    rainy_days = db.Column(db.Integer)
    rainfall = db.Column(db.Float)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    valid_from = db.Column(db.String(7))
    valid_until = db.Column(db.String(7))
    measurements = db.relationship("MonthlyMeasurements", cascade="all, delete-orphan")
    weights = db.relationship("Weight", cascade="all, delete-orphan")


class Weight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.Integer, db.ForeignKey('location.id'))
    year = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Float)

