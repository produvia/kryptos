# -*- coding: utf-8 -*-
import os
import json
from flask import (
    Blueprint,
    redirect,
    current_app,
    render_template,
    request,
    url_for,
    flash,
)
from flask_user import current_user, login_required
from google.cloud import storage

from app.extensions import db
from app.forms import forms
from app.models import User, UserExchangeAuth
from app.utils.auth import upload_user_auth, delete_user_auth


blueprint = Blueprint("account", __name__, url_prefix="/account")


def telegram_auth_url():
    return os.path.join(
        current_app.config["FRONTEND_URL"], "/account/telegram/authorize"
    )


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


@blueprint.route("/exchanges/remove", methods=["POST"])
def remove_exchange_auth():
    remove_form = forms.UserExchangeKeyRemoveForm()
    remove_form.exchange_name.choices = [
        (e.exchange, e.exchange) for e in current_user.authenticated_exchanges
    ]

    if remove_form.validate():
        exchange_name = remove_form.exchange_name.data
        current_app.logger.info(
            f"Removing new auth key for {current_user} {exchange_name}"
        )

        # destroy_user_exchange_key(current_user.id, exchange_name)
        delete_user_auth(current_user.uuid, exchange_name)

        auth_ref = UserExchangeAuth.query.filter_by(
            user=current_user, exchange=exchange_name
        ).first()
        db.session.delete(auth_ref)
        db.session.commit()

    return redirect(url_for("account.manage_exchanges"))


@blueprint.route("/exchanges", methods=["GET", "POST"])
@login_required
def manage_exchanges():
    new_form = forms.UserExchangeKeysForm()
    # remove_form = forms.UserExchangeKeysForm()
    remove_form = forms.UserExchangeKeyRemoveForm()
    remove_form.exchange_name.choices = [
        (e.exchange, e.exchange) for e in current_user.authenticated_exchanges
    ]

    if request.method == "POST" and new_form.validate():

        exchange_dict = {
            "name": new_form.exchange.data,
            "key": new_form.api_key.data,
            "secret": new_form.api_secret.data,
        }
        current_app.logger.info(
            f'Adding new auth key for {current_user} {exchange_dict["name"]}'
        )

        exchange_name = new_form.exchange.data.lower()

        existing = UserExchangeAuth.query.filter_by(
            user=current_user, exchange=exchange_name
        ).first()

        if existing is not None:
            flash(
                f"You have already provided an API key for {exchange_name}, please remove it before adding a new one",
                "error",
            )
            return redirect(url_for("account.manage_exchanges"))

        blob_name, auth_bucket = upload_user_auth(exchange_dict, current_user.uuid)
        user = current_user
        exchange_ref = UserExchangeAuth(exchange=exchange_name, user=user)

        db.session.add(exchange_ref)
        db.session.commit()

        current_app.logger.debug(
            "Encrypted auth {} uploaded to {} bucket.".format(blob_name, auth_bucket)
        )

        return redirect(url_for("strategy.build_strategy"))

    return render_template(
        "account/user_exchanges.html", new_form=new_form, remove_form=remove_form
    )
