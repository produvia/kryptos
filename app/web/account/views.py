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


blueprint = Blueprint('account', __name__, url_prefix='/account')

def telegram_auth_url():
    return os.path.join(current_app.config['FRONTEND_URL'], '/account/telegram/authorize')

@blueprint.route('/')
def user_account():
    return render_template('account/dashboard.html', telegram_auth_url=telegram_auth_url(), telegram_bot=current_app.config['TELEGRAM_BOT'])

@blueprint.route('//telegram')
def prompt_telegram():
    return render_template('account/telegram_auth.html', telegram_auth_url=telegram_auth_url(), telegram_bot=current_app.config['TELEGRAM_BOT'])

@blueprint.route('//telegram/logout')
@login_required
def telegram_logout():
    user = current_user
    user.unlink_telegram()

    flash('Sucessfully logged out of Telegram!')
    return render_template('account/dashboard.html')

@blueprint.route('//telegram/authorize')
@login_required
def telegram_authorize():
    telegram_id = request.args.get('id')
    username = request.args.get('username')
    photo_url = request.args.get('photo_url')
    auth_date = request.args.get('auth_date')
    has = request.args.get('hash)')

    existing_linked_user = User.query.filter_by(telegram_id=telegram_id).first()
    if existing_linked_user is not None:
        bot_name = current_app.config['TELEGRAM_BOT']
        flash(f'Cannot link telegram account to more than one kryptos account.\n You can unlink your telegram account by sending "/logout" to @{bot_name} in telegram', category='error')
        return redirect(url_for('account.user_account'))


    user = current_user
    user.telegram_id = telegram_id
    user.telegram_username = username
    user.telegram_photo = photo_url
    user.telegram_auth_date = auth_date

    db.session.add(user)
    db.session.commit()
    flash('Sucessfully logged in with Telegram!')

    message = "Thanks for signing up with Kryptos!\nType /menu to have a look around."

    bot_utils.send_to_user(message, user)
    return render_template('account/dashboard.html')


@blueprint.route('/strategies')
@login_required
def user_strategies():
    return render_template('account/strategies.html')


@blueprint.route('/exchanges', methods=['GET', 'POST'])
@login_required
def manage_exchanges():
    form = forms.UserExchangeKeysForm()

    if request.method == 'POST' and form.validate():

        exchange_dict = {
            'name': form.exchange.data,
            'key': form.api_key.data,
            'secret': form.api_secret.data
        }

        root = os.path.expanduser
        base = 'catalyst/data/exchanges'
        exchange_dir = os.path.join(base, form.exchange.data)
        file_name = 'auth_' + str(current_user.id) + '.json'
        user_auth_file = os.path.join(exchange_dir, file_name)

        if not os.path.exists(exchange_dir):
            os.makedirs(exchange_dir)


        with open(user_auth_file, 'w') as f:
            current_app.logger.error(f'Writing to {user_auth_file}')
            json.dump(exchange_dict, f)


        return redirect(url_for('strategy.build_strategy'))

    return render_template('account/user_exchanges.html', form=form)
