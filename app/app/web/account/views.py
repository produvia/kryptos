# -*- coding: utf-8 -*-
import os
import json
from flask import Blueprint, redirect, current_app, render_template, request, url_for, flash
from flask_user import current_user, login_required
from google.cloud import storage

from app.extensions import db
from app.forms import forms
from app.models import User
from app.utils import upload_user_auth


blueprint = Blueprint("account", __name__, url_prefix="/account")


def telegram_auth_url():
    return os.path.join(current_app.config["FRONTEND_URL"], "/account/telegram/authorize")


@blueprint.route("/")
def user_account():
    return render_template(
        "account/dashboard.html",
        telegram_auth_url=telegram_auth_url(),
        telegram_bot=current_app.config["TELEGRAM_BOT"],
    )


@blueprint.route("/telegram")
def prompt_telegram():
    return render_template(
        "account/telegram_auth.html",
        telegram_auth_url=telegram_auth_url(),
        telegram_bot=current_app.config["TELEGRAM_BOT"],
    )


@blueprint.route("/telegram/logout")
@login_required
def telegram_logout():
    user = current_user
    user.unlink_telegram()

    flash("Sucessfully logged out of Telegram!")
    return render_template("account/dashboard.html")


@blueprint.route("/telegram/authorize")
@login_required
def telegram_authorize():
    telegram_id = request.args.get("id")
    username = request.args.get("username")
    photo_url = request.args.get("photo_url")
    auth_date = request.args.get("auth_date")
    has = request.args.get("hash)")

    existing_linked_user = User.query.filter_by(telegram_id=telegram_id).first()
    if existing_linked_user is not None:
        bot_name = current_app.config["TELEGRAM_BOT"]
        flash(
            f'Cannot link telegram account to more than one kryptos account.\n You can unlink your telegram account by sending "/logout" to @{bot_name} in telegram',
            category="error",
        )
        return redirect(url_for("account.user_account"))

    user = current_user
    user.telegram_id = telegram_id
    user.telegram_username = username
    user.telegram_photo = photo_url
    user.telegram_auth_date = auth_date

    db.session.add(user)
    db.session.commit()
    flash("Sucessfully logged in with Telegram!")

    message = "Thanks for signing up with Kryptos!\nType /menu to have a look around."

    # TODO send message using updater
    return render_template("account/dashboard.html")


@blueprint.route("/strategies")
@login_required
def user_strategies():
    return render_template("account/strategies.html")


@blueprint.route("/exchanges", methods=["GET", "POST"])
@login_required
def manage_exchanges():
    form = forms.UserExchangeKeysForm()

    if request.method == "POST" and form.validate():

        exchange_dict = {
            "name": form.exchange.data,
            "key": form.api_key.data,
            "secret": form.api_secret.data,
        }

        blob_name, auth_bucket = upload_user_auth(exchange_dict, current_user.id)

        current_app.logger.warn(
            "Exchange Auth {} uploaded to {} bucket.".format(blob_name, auth_bucket)
        )

        return redirect(url_for("strategy.build_strategy"))

    return render_template("account/user_exchanges.html", form=form)
