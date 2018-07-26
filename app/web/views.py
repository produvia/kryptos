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
blueprint = Blueprint('web', __name__, url_prefix='/')

def telegram_auth_url():
    return os.path.join(current_app.config['FRONTEND_URL'], '/account/telegram/authorize')


@blueprint.route('/')
def home_page():
    return render_template('public/landing.html', current_user=current_user)

@blueprint.route('/account')
def user_account():
    return render_template('account/dashboard.html', telegram_auth_url=telegram_auth_url(), telegram_bot=current_app.config['TELEGRAM_BOT'])

@blueprint.route('/account/telegram')
def prompt_telegram():
    return render_template('account/telegram_auth.html', telegram_auth_url=telegram_auth_url(), telegram_bot=current_app.config['TELEGRAM_BOT'])

@blueprint.route('/account/telegram/logout')
@login_required
def telegram_logout():
    user = current_user
    user.unlink_telegram()

    flash('Sucessfully logged out of Telegram!')
    return render_template('account/dashboard.html')

@blueprint.route('/account/telegram/authorize')
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
        return redirect(url_for('web.user_account'))


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


@blueprint.route('account/strategies')
@login_required
def user_strategies():
    return render_template('account/strategies.html')

@blueprint.route('backtest/strategy/<strat_id>', methods=['GET'])
def public_backtest_status(strat_id):
    return render_template('account/strategy_status.html', strat_id=strat_id)


@blueprint.route('account/strategy/<strat_id>', methods=['GET'])
@login_required
def strategy_status(strat_id):
    strat = StrategyModel.query.filter_by(id=strat_id).first_or_404()
    if not strat in current_user.strategies:
        return 401
    current_app.logger.error(strat.id)
    return render_template('account/strategy_status.html', strat_id=strat_id)


@blueprint.route('/_get_group_indicators/')
def _get_group_indicators():
    group = request.args.get('group', '01', type=str)
    indicators = forms.get_indicators_by_group(group)
    return jsonify(indicators)

@blueprint.route('/_get_indicator_params/')
def _get_indicator_params():
    indicator_abbrev = request.args.get('indicator', '01', type=str)
    params_obj = forms._get_indicator_params(indicator_abbrev)
    return  jsonify(params_obj)


def process_trading_form(form):
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
    return trading_dict

def process_indicator_form(form):
    indicator_dict = {
        'name': form.indicator_name.data,
        'symbol': form.symbol.data,
        'label': form.custom_label.data
    }
    return indicator_dict
@blueprint.route("account/strategy", methods=['GET', 'POST'])
def build_strategy():
    form = forms.TradeInfoForm()
    if form.validate_on_submit():

        trading_dict = process_trading_form(form)

        live = form.trade_type in ['live', 'paper']
        simulate_orders = form.trade_type == 'live'

        session['strat_dict'] = {
            'name': form.name.data,
            'trading': trading_dict,
            'live': live,
            'simulate_orders': simulate_orders

        }

        return redirect(url_for('web.build_indicators'))

    return render_template('strategy/trading.html', form=form)

@blueprint.route('account/strategy/indicators', methods=['GET', 'POST'])
def build_indicators():
    if not session.get('strat_dict', {})['trading']:
        return redirect(url_for('web.build_strategy'))
    indicator_form = forms.IndicatorInfoForm()
    indicator_form.group.choices = forms.indicator_group_name_selectors()
    indicator_form.indicator_name.choices = forms.all_indicator_selectors()

    if request.method == 'POST' and indicator_form.validate_on_submit():

        indicator_dict = process_indicator_form(indicator_form)

        strat_indicators = session['strat_dict'].get('indicators', [])
        strat_indicators.append(indicator_dict)

        session['strat_dict']['indicators'] = strat_indicators

        strat_dict = session['strat_dict']
        live, simulate_orders = strat_dict['live'], strat_dict['simulate_orders']

        job_id, queue_name = worker.queue_strat(json.dumps(strat_dict), current_user.id, live, simulate_orders)

        return redirect(url_for('web.strategy_status', strat_id=job_id))

    if indicator_form.validate_on_submit():
        pass

    return render_template('strategy/indicators.html', form=indicator_form)


@blueprint.route('account/exchanges', methods=['GET', 'POST'])
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


        return redirect(url_for('web.build_strategy'))

    return render_template('account/user_exchanges.html', form=form)
