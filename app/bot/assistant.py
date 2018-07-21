import logging
import os
import json
from textwrap import dedent
import datetime

from flask import Blueprint, request, current_app
from flask_assistant import Assistant, tell, event, context_manager
from flask_assistant.response import _Response
import talib as ta
import talib.abstract as ab

from app.bot.response import ask, inline_keyboard
from kryptos.worker import worker

blueprint = Blueprint('bot', __name__, url_prefix='/bot')
assist = Assistant(blueprint=blueprint)


logging.getLogger('flask_assistant').setLevel(logging.DEBUG)

EXISTING_STRATS = [
    ('Bollinger Bands (BBANDS)', 'BBANDS'),
    ('Stop and Reverse (SAR)', 'SAR'),
    ('Moving Average Convergence/Divergence (MACD)', 'MACD'),
    ('Moving Average Convergence/Divergence Fix (MACDFIX)', 'MACDFIX'),
    ('On Balance Volume (OBV)', 'OBV'),
    ('Relative Strength Index (RSI)', 'RSI'),
    ('Stochastic (STOCH)', 'STOCH')
]


def get_user_from_request():
    platform_data =  request.json.get('originalRequest', {}).get('data', {})
    if not platform_data:
        return {'first_name': 'USER', 'id': 34567}

    if platform_data.get('message'):
        return platform_data['message']['from']

    elif platform_data.get('callback_query'):
        return platform_data['callback_query']['from']


@assist.action('Default Welcome Intent')
def welcome_message():
    user_name = get_user_from_request()['first_name']
    msg = f"Hello {user_name}! I’m Kryptos AI, your virtual assistant to buy and sell bitcoin and other coins."
    return ask(msg)



@assist.action('activity-menu')
def show_menu():
    user_name = get_user_from_request()['first_name']
    speech = f"""\
    Hi {user_name}. Let's get started. Please select a number or text me the named
    1. Launch New Strategy
    2. Run Performance Report
    3. Update Goals
    4. Upgrade SKills
    5. Adjust Kryptos"""
    return ask(speech).with_quick_reply('1', '2', '3', '4', '5')


# @assist.context('activity-selection')
@assist.action('new-strategy')
def display_available_strats():
    # speech = """\
    # Great. Which strategy do you wish to try?
    # 1. Simple Moving Average (SMA) Crossover
    # 2. Relative Strength Index (RSI)
    # 3. Explore Momentum Indicators
    # """
    resp = inline_keyboard("Which strategy do you wish to try?")
    for i in EXISTING_STRATS:
        resp.add_button(*i)
    return resp



@assist.action('new-strategy-display-momentum')
def display_momentum_indicators():
    momentum_indicators = ta.get_function_groups()['Momentum Indicators']
    speech = "Here are all the possible Momentum Indicators you can use:"
    for i in range(len(momentum_indicators)):
        abbrev = momentum_indicators[i]

        func = getattr(ab, abbrev)
        name = func.info['display_name']
        speech += f'\n{i+1}. {abbrev} - {name}'
    return ask(speech)

@assist.action('new-strategy-select')
def select_strategy(existing_strategy):
    backtest_dict = {'trading': {}, 'indicators': [{"name": existing_strategy}]}

    # Can't use today as the end date bc data bundles are updated daily,
    # so current market data won't be avialable for backtest until the following day
    # use past week up to yesterday
    back_start = datetime.datetime.today() - datetime.timedelta(days=8)
    back_end = datetime.datetime.today() - datetime.timedelta(days=1)

    backtest_dict['trading']['START'] = datetime.datetime.strftime(back_start, '%Y-%m-%d')
    backtest_dict['trading']['END'] = datetime.datetime.strftime(back_end, '%Y-%m-%d')

    backtest_id, _ = worker.queue_strat(json.dumps(backtest_dict), live=False, simulate_orders=True)
    backtest_url = os.path.join(current_app.config['FRONTEND_URL'], 'monitor', backtest_id)



    speech = f'You selected {existing_strategy}!\n\n Would you like to launch it?\n\n Here’s a preview of how well this strategy performed in the last 7 days'

    resp = inline_keyboard(dedent(speech))
    resp.add_button('View Past Performance', url=backtest_url)

    return resp.with_quick_reply('yes', 'no')

@assist.action('new-strategy-select-yes')
def launch_strategy(existing_strategy):
    # will fill with default values
    start = datetime.datetime.today()
    end = start + datetime.timedelta(days=7)


    strat_dict = {'indicators': [{"name": existing_strategy}]}
    strat_dict['START'] = datetime.datetime.strftime(start, '%Y-%m-%d')
    strat_dict['END'] = datetime.datetime.strftime(end, '%Y-%m-%d')

    job_id, _ = worker.queue_strat(json.dumps(strat_dict), live=True, simulate_orders=True)


    speech = f"""\
    Great! The strategy is now live and will run for the next 7 days.

    You can view your strategy's progress by clicking the link below and I will keep you updated on how it performs.
    """
    url = os.path.join(current_app.config['FRONTEND_URL'], 'monitor', job_id)
    resp = inline_keyboard(dedent(speech))
    resp.add_button('View your Strategy', url=url)
    return resp
