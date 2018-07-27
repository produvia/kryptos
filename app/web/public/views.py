# -*- coding: utf-8 -*-
import os
import json
from flask import send_file, Blueprint, redirect, current_app, render_template, request, url_for, flash, jsonify, session
from flask_user import current_user, login_required

from app.extensions import db
from app.forms import forms
from kryptos.worker import worker
from app.models import User, StrategyModel
from app.bot import bot_utils

# Grouping 2 blueprints together
blueprint = Blueprint('public', __name__, url_prefix='/')


@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)
