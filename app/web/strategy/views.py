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


blueprint = Blueprint('strategy', __name__, url_prefix='/strategy')


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

@blueprint.route('/strategy/<strat_id>', methods=['GET'])
@login_required
def strategy_status(strat_id):
    strat = StrategyModel.query.filter_by(id=strat_id).first_or_404()
    if not strat in current_user.strategies:
        return 401
    current_app.logger.error(strat.id)
    return render_template('account/strategy_status.html', strat_id=strat_id)

@blueprint.route('backtest/strategy/<strat_id>', methods=['GET'])
def public_backtest_status(strat_id):
    return render_template('account/strategy_status.html', strat_id=strat_id)


@blueprint.route("/build", methods=['GET', 'POST'])
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

        return redirect(url_for('strategy.build_indicators'))

    return render_template('strategy/trading.html', form=form)

@blueprint.route('build/indicators', methods=['GET', 'POST'])
def build_indicators():

    strat_dict = session.get('strat_dict', {})
    if not strat_dict.get('trading', {}):
        return redirect(url_for('account.build_strategy'))
    indicator_form = forms.IndicatorInfoForm()
    indicator_form.group.choices = forms.indicator_group_name_selectors()
    indicator_form.indicator_name.choices = forms.all_indicator_selectors()

    if request.method == 'POST' and indicator_form.validate_on_submit():

        indicator_dict = process_indicator_form(indicator_form)
        params = {}

        # get params outside of wtf form
        for key in request.form.keys():
            if 'param-' in key:
                name, val = key.strip('param-'), request.form.get(key)
                params[name] = val

        indicator_dict['params'] = params

        strat_indicators = session['strat_dict'].get('indicators', [])
        strat_indicators.append(indicator_dict)

        session['strat_dict']['indicators'] = strat_indicators


        # render new form if adding another
        if indicator_form.add_another.data:
            return render_template('strategy/indicators.html', form=indicator_form)


        # remove from session if submitting strat
        strat_dict = session.pop('strat_dict')
        live, simulate_orders = strat_dict['live'], strat_dict['simulate_orders']

        job_id, queue_name = worker.queue_strat(json.dumps(strat_dict), current_user.id, live, simulate_orders)

        return redirect(url_for('account.strategy_status', strat_id=job_id))

    return render_template('strategy/indicators.html', form=indicator_form)
