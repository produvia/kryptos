# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint

blueprint = Blueprint("public", __name__, static_folder="../static")


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Landing page for the web/html blueprint"""
    return "Kryptos Web Page"
