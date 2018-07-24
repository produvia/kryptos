# -*- coding: utf-8 -*-
import os
import json
from flask import send_file, Blueprint, redirect, current_app, render_template, request, url_for
from flask_user import current_user, login_required

from app.extensions import db
from app.forms.forms import UserExchangeKeysForm, TradeInfoForm
from kryptos.worker import worker
from app.models import User, Strategy

# Grouping 2 blueprints together
blueprint = Blueprint('web', __name__, url_prefix='/')



@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)


@blueprint.route('account/strategy/<strat_id>', methods=['GET'])
def strategy_status(strat_id):
    return render_template('account/strategy_status.html', strat_id=strat_id)


@blueprint.route("account/strategy", methods=['GET', 'POST'])
def build_strategy():
    form = TradeInfoForm()
    if form.validate_on_submit():

        trading_dict = {
           "EXCHANGE": form.exchange.data,
           "ASSET": form.asset.data,
           "DATA_FREQ": form.data_freq.data,
           "HISTORY_FREQ": form.history_freq.data,
           "CAPITAL_BASE": form.capital_base.data,
           "BASE_CURRENCY": form.base_currency.data,
           "START": form.start.data,
           "END": form.end.data,
           "BARS": form.bar_period.data,
           "ORDER_SIZE": form.order_size.data,
           "SLIPPAGE_ALLOWED": form.slippage_allowed.data

        }

        strat_dict = {
            'name': form.name.data,
            'trading': trading_dict
        }

        live = form.trade_type in ['live', 'paper']
        simulate_orders = form.trade_type == 'live'

        job_id, queue_name = worker.queue_strat(json.dumps(strat_dict), live, simulate_orders)

        return redirect(url_for('web.strategy_status', strat_id=job_id))

    return render_template('account/build_strategy.html', form=form)


@blueprint.route('account/exchanges', methods=['GET', 'POST'])
@login_required
def manage_exchanges():
    form = UserExchangeKeysForm()

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


        return redirect(url_for('web.build_strategy'))

    return render_template('account/user_exchanges.html', form=form)
