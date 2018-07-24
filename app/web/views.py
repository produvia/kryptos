# -*- coding: utf-8 -*-
import os
from flask import send_file, Blueprint, redirect, current_app, render_template
from flask_user import current_user
from kryptos.utils.outputs import in_docker
import requests

blueprint = Blueprint('main', __name__, url_prefix='/')

@blueprint.route('/')
def home_page():
    return render_template('main/landing.html', current_user=current_user)
