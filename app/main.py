import asyncio
from collections import defaultdict
from datetime import date

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash
from flask import jsonify
from flask import request
from flask_login import login_required, current_user
from webargs import fields, validate
from webargs.flaskparser import use_args

from . import db
from .scraping import load_historical_data
from .models import Location
from .models import MonthlyMeasurements
from .models import Weight

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


# Return validation errors as JSON
@main.errorhandler(422)
@main.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)


@main.route('/locations')
def locations():
    locations = Location.query.all()
    return render_template('locations.html', current_user=current_user, locations=locations)


@main.route('/locations/new')
@login_required
def new_location():
    return render_template('new_location.html', current_user=current_user)


@main.route('/locations', methods=['POST'])
@login_required
@use_args(
        {
            "name": fields.Str(required=True, validate=validate.Length(min=4, max=100)),
            "valid_from": fields.Str(required=True, validate=validate.Length(equal=7)),
            "valid_until": fields.Str(required=True, validate=validate.Length(equal=7)),
        },
        location='form')
def create_location(args):
    location = Location(
            name=args['name'],
            valid_from=args['valid_from'],
            valid_until=args['valid_until'])

    db.session.add(location)
    db.session.commit()

    flash('The new location was created.')
    return 'Ok'


@main.route('/locations/<id>/edit')
@login_required
def edit_location(id):
    location = Location.query.filter_by(id=id).first()
    return render_template('edit_location.html', current_user=current_user, location=location)


@main.route('/locations/<id>/delete')
@login_required
def delete_location(id):
    location = Location.query.filter_by(id=id).first()
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted.')
    return redirect('/locations')


@main.route('/locations/<id>', methods=['POST'])
@login_required
@use_args(
        {
            "name": fields.Str(required=True, validate=validate.Length(min=4, max=100)),
            "valid_from": fields.Str(required=True, validate=validate.Length(equal=7)),
            "valid_until": fields.Str(required=True, validate=validate.Length(equal=7)),
        },
        location='form')
def update_location(args, id):
    location = Location.query.filter_by(id=id).first()

    location.name = args['name']
    location.valid_from = args['valid_from']
    location.valid_until = args['valid_until']

    db.session.commit()

    flash('The location was updated.')
    return 'Ok'


@main.route('/locations/<id>')
def location(id):
    location = Location.query.filter_by(id=id).first()
    return render_template('location.html', current_user=current_user, location=location)


@main.route('/measurements/new')
@login_required
def new_measurement():
    location_id = request.args['location']
    location = Location.query.filter_by(id=location_id).first()
    return render_template('new_measurement.html', current_user=current_user, location=location)


@main.route('/measurements', methods=['POST'])
@login_required
@use_args(
        {
            "month": fields.Str(required=True, validate=validate.Length(equal=7)),
            "average_temp": fields.Float(required=True, validate=lambda val: val >= -273.15),
            "average_min_temp": fields.Float(required=True, validate=lambda val: val >= -273.15),
            "average_max_temp": fields.Float(required=True, validate=lambda val: val >= -273.15),
            "sunshine_hours": fields.Float(required=True, validate=validate.Range(0, 744)),
            "rainfall": fields.Float(required=True, validate=lambda val: val >= 0),
            "rainy_days": fields.Integer(required=True, validate=validate.Range(0, 31)),
            "average_snow_coverage": fields.Float(required=True, validate=lambda val: val >= 0),
        },
        location='form')
def create_measurement(args):
    location_id = request.args['location']

    measurement = MonthlyMeasurements(
            location=location_id,
            year=int(args['month'][0:4]),
            month=int(args['month'][5:7]),
            average_temp=args['average_temp'],
            average_min_temp=args["average_min_temp"],
            average_max_temp=args["average_max_temp"],
            sunshine_hours=args["sunshine_hours"],
            rainfall=args["rainfall"],
            rainy_days=args["rainy_days"],
            average_snow_coverage=args["average_snow_coverage"])

    db.session.add(measurement)
    db.session.commit()

    flash('The new measurement was created.')
    return 'Ok'


@main.route('/locations/<location_id>/load_data', methods=["POST"])
@login_required
def load_data(location_id):
    location = Location.query.filter_by(id=location_id).first()
    overwrite_existing = request.args['overwrite_existing']
    overwrite_existing = overwrite_existing.lower() in ('true', '1', 't', 'y', 'yes')

    asyncio.run(load_historical_data(location, overwrite_existing))

    flash('Historical data loaded successfully.')
    return 'Ok'


@main.route('/weights')
def weights():
    locations = Location.query.all()

    if len(locations) == 0:
        return render_template(
                'weights.html',
                current_user=current_user,
                locations=locations,
                min_year=date.today().year,
                max_year=date.today().year,
                weights=defaultdict(lambda: {}))


    min_year = min(int(l.valid_from[:4]) for l in locations)
    max_year = max(int(l.valid_until[:4]) for l in locations)

    weights = defaultdict(lambda: {})
    for location in locations:
        for weight in location.weights:
            weights[location.id][weight.year] = weight.value

    return render_template(
            'weights.html',
            current_user=current_user,
            locations=locations,
            min_year=min_year,
            max_year=max_year,
            weights=weights)


@main.route('/weights', methods=["POST"])
@login_required
def update_weights():
    locations = Location.query.all()

    location_weights = {}
    for location in locations:
        location_weights[location.id] = location.weights

    for key in request.form:
        location_id_str, year_str = key.split('-')
        location_id = int(location_id_str)
        year = int(year_str)
        value = float(request.form.get(key)) if request.form.get(key) != '' else None

        weight = next((w for w in location_weights[location_id] if w.year == year), None)
        if weight:
            weight.value = value
            db.session.commit()
        else:
            weight = Weight(location=location_id, year=year, value=value)
            db.session.add(weight)
            db.session.commit()

    flash('Weights updated successfully.')
    return 'ok'


