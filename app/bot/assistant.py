import logging
import os
import json
from textwrap import dedent
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
    if not request.json.get('originalRequest'):
        return {'first_name': 'USER', 'id': 34567}
    return request.json['originalRequest']['data']['message']['from']


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
    speech = f'You selected {existing_strategy}!\n\n Would you like to launch it?'
    return ask(speech).with_quick_reply('yes', 'no')

@assist.action('new-strategy-select-yes')
def launch_strategy(existing_strategy):
    # will fill with default values
    strat_dict = {
        "indicators": [
            {
                "name": existing_strategy,
            }
        ]
    }

    job_id, _ = worker.queue_strat(json.dumps(strat_dict), live=False, simulate_orders=True)

    #TODO run strat as paper/live and get past 7 days performance from backtest

    speech = """\
    Great! The strategy is live now and will run for the next 7 days.
    Here’s a preview of how well this strategy performed in the last 7 days: kryptos.io/hk236g.\n\n
    You can view your strategy's progress by clicking the link below and I will keep you updated on how it performs.
    """
    url = os.path.join(current_app.config['FRONTEND_URL'], 'monitor', job_id)
    resp = inline_keyboard(dedent(speech))
    resp.add_button('View your Strategy', url=url)
    return resp
