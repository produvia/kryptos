# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flask_user import current_user

# Grouping 2 blueprints together
blueprint = Blueprint('public', __name__, url_prefix='/')


@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)
