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

from app.models import User
from app.bot.response import ask, inline_keyboard
from kryptos.worker import worker

blueprint = Blueprint('bot', __name__, url_prefix='/bot')
assist = Assistant(blueprint=blueprint)


logging.getLogger('flask_assistant').setLevel(logging.INFO)

EXISTING_STRATS = [
    ('Bollinger Bands (BBANDS)', 'BBANDS'),
    ('Stop and Reverse (SAR)', 'SAR'),
    ('Moving Average Convergence/Divergence (MACD)', 'MACD'),
    ('Moving Average Convergence/Divergence Fix (MACDFIX)', 'MACDFIX'),
    ('On Balance Volume (OBV)', 'OBV'),
    ('Relative Strength Index (RSI)', 'RSI'),
    ('Stochastic (STOCH)', 'STOCH')
]


# TODO possibly use tleegram chat_id
def get_user():
    telegram_id = get_message_payload()['id']
    user = User.query.filter_by(telegram_id=telegram_id).first()
    current_app.logger.debug(f'Got user {user}')
    return user

def get_first_name():
    name =  get_message_payload().get('first_name', None)
    if name is not None:
        return name
    return ''



def get_message_payload():
    platform_data =  request.json.get('originalRequest', {}).get('data', {})
    current_app.logger.info(platform_data)
    if not platform_data:
        return {'first_name': 'DialogFlow', 'id': 111}

    if platform_data.get('message'):
        return platform_data['message']['from']

    elif platform_data.get('callback_query'):
        return platform_data['callback_query']['from']


@assist.action('Default Welcome Intent')
def welcome_message():
    user_name = get_first_name()
    msg = f"Hello {user_name}! I’m Kryptos AI, your virtual investment assistant that manages your cryptocurrency portfolio and automates your cryptocurrency trading"

    if get_user() is None:
        current_app.logger.info('Prompting user to login')
        msg += f"\n\nBefore we can get started, you'll need to create a free Kryptos account and authentiate with Telegram"
        resp = inline_keyboard(msg)
        url = os.path.join(current_app.config['FRONTEND_URL'], 'account/telegram')
        resp.add_button('Create an account', url=current_app.config['FRONTEND_URL'])
        return resp

    return ask(msg)


@assist.action('account-unlink')
def unlink_telegram_confirm():
    speech = """\
    Are you sure you want to unlink your telegram account from Kryptos?
    You won't be able to receive updates from me anymore.
    """

    return ask(dedent(speech)).with_quick_reply('yes', 'no')

@assist.action('account-unlink-yes')
def unlink_telegram_account():
    user = get_user()
    user.unlink_telegram()
    speech = f"""\
    Your account is now unlinked
    You can always re-link at {current_app.config['FRONTEND_URL']}
    """
    return tell(dedent(speech))


@assist.action('activity-menu')
def show_menu():
    user_name = get_first_name()
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

@assist.context('new-strategy-select-followup')
@assist.action('new-strategy-select')
def select_strategy(existing_strategy):
    # TODO determine exchange
    backtest_dict = {'trading': {'EXCHANGE': 'bitfinex'}, 'indicators': [{"name": existing_strategy}]}
    backtest_dict['name'] = f"{existing_strategy} Backtest"

    # Can't use today as the end date bc data bundles are updated daily,
    # so current market data won't be avialable for backtest until the following day
    # use past week up to yesterday
    back_start = datetime.datetime.today() - datetime.timedelta(days=100)
    back_end = datetime.datetime.today() - datetime.timedelta(days=7)


    backtest_dict['trading']['START'] = datetime.datetime.strftime(back_start, '%Y-%m-%d')
    backtest_dict['trading']['END'] = datetime.datetime.strftime(back_end, '%Y-%m-%d')



    backtest_id, _ = worker.queue_strat(json.dumps(backtest_dict), user_id=None, live=False, simulate_orders=True)
    current_app.logger.info(f'Queues Strat {backtest_id}')
    backtest_url = os.path.join(current_app.config['FRONTEND_URL'], 'strategy/backtest/strategy/', backtest_id)



    speech = f'You selected {existing_strategy}!\n\n Would you like to launch it?\n\n Here’s a preview of how well this strategy performed over the past 100 days'

    resp = inline_keyboard(dedent(speech))
    resp.add_button('View Past Performance', url=backtest_url)

    return resp.with_quick_reply('yes', 'no')

@assist.action('new-strategy-select-yes')
def launch_strategy(existing_strategy):
    # will fill with default values
    start = datetime.datetime.today()
    end = start + datetime.timedelta(days=7)

    user = get_user()
    strat_dict = {'trading': {}, 'indicators': [{"name": existing_strategy}]}
    strat_dict['trading']['START'] = datetime.datetime.strftime(start, '%Y-%m-%d')
    strat_dict['trading']['END'] = datetime.datetime.strftime(end, '%Y-%m-%d')
    strat_dict['name'] = f"{existing_strategy}-Paper"



    job_id, _ = worker.queue_strat(json.dumps(strat_dict), user.id, live=True, simulate_orders=True)
    url = os.path.join(current_app.config['FRONTEND_URL'], 'account/strategy/', job_id)

    speech = f"""\
    Great! The strategy is now live and will run for the next 7 days.

    You can view your strategy's progress by clicking the link below and I will keep you updated on how it performs.
    """

    resp = inline_keyboard(dedent(speech))
    resp.add_button('View your Strategy', url=url)
    return resp
