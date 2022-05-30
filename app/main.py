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
from .models import Location

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
def new_location():
    return render_template('new_location.html', current_user=current_user)


@main.route('/locations', methods=['POST'])
@use_args(
        {
            "name": fields.Str(required=True, validate=validate.Length(min=4, max=100)),
            "valid_from": fields.Str(required=True, validate=validate.Length(equal=7)),
            "valid_until": fields.Str(required=True, validate=validate.Length(equal=7)),
        },
        location='form')
def create_location(args):
    print(args)

    flash('The new location was created.')
    return ''
    return redirect(url_for('main.locations'))
