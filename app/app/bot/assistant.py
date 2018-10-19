import logging
import os
import json
from textwrap import dedent
import datetime

from flask import Blueprint, current_app
from flask_assistant import Assistant, tell, event, context_manager
import talib as ta
import talib.abstract as ab

from app.bot.response import ask, inline_keyboard
from app.bot import utils

blueprint = Blueprint("bot", __name__, url_prefix="/bot")
assist = Assistant(blueprint=blueprint)


logging.getLogger("flask_assistant").setLevel(logging.INFO)


@assist.action("Default Welcome Intent")
def welcome_message():
    user_name = utils.get_first_name()
    msg = f"Hello {user_name}! I’m Kryptos AI, your virtual investment assistant that manages your cryptocurrency portfolio and automates your cryptocurrency trading"

    if utils.get_user() is None:
        current_app.logger.info("Prompting user to login")
        msg += f"\n\nBefore we can get started, you'll need to create a free Kryptos account and authentiate with Telegram"
        resp = inline_keyboard(msg)
        url = os.path.join(current_app.config["FRONTEND_URL"], "account/telegram")
        resp.add_button("Create an account", url=url)
        return resp

    return ask(msg)


@assist.action("account-unlink")
def unlink_telegram_confirm():
    speech = """\
    Are you sure you want to unlink your telegram account from Kryptos?
    You won't be able to receive updates from me anymore.
    """

    return ask(dedent(speech)).with_quick_reply("yes", "no")


@assist.action("account-unlink-yes")
def unlink_telegram_account():
    user = utils.get_user()
    user.unlink_telegram()
    speech = f"""\
    Your account is now unlinked
    You can always re-link at {current_app.config['FRONTEND_URL']}
    """
    return tell(dedent(speech))


@assist.action("activity-menu")
def show_menu():
    user_name = utils.get_first_name()
    resp = inline_keyboard(f"Hi {user_name}. Let's get started")
    resp.add_button("Launch New Strategy", "new_strat")
    resp.add_button("Run performance report", "performance_report")
    resp.add_button("Update Goals", "update_goals")
    resp.add_button("Upgrade Skills", "upgrade_skills")
    resp.add_button("Adjust Kryptos", "adjust_keytpos")

    return resp


@assist.action("new-strategy-display-momentum")
def display_momentum_indicators():
    momentum_indicators = ta.get_function_groups()["Momentum Indicators"]
    speech = "Here are all the possible Momentum Indicators you can use:"
    for i in range(len(momentum_indicators)):
        abbrev = momentum_indicators[i]

        func = getattr(ab, abbrev)
        name = func.info["display_name"]
        speech += f"\n{i+1}. {abbrev} - {name}"
    return ask(speech)


#########################
# BUILD STRATEGY CONFIG #
#########################


@assist.action("new-strategy")
def display_available_strats():
    context_manager.add("strat-config-data")
    resp = inline_keyboard("Which strategy do you wish to try?")
    for i in utils.EXISTING_STRATS:
        resp.add_button(*i)
    return resp


@assist.context("strat-config-data")
@assist.action("new-strategy-select-strat")
def select_strategy(existing_strategy):
    return event("strat-config-start", existing_strategy=existing_strategy)


@assist.context("strat-config-data")
@assist.action("strat-config", events=["strat-config-start"])
def prompt_exchange(existing_strategy):
    context_manager.set("strat-config-data", "existing_strategy", existing_strategy)
    speech = "Which exchange would you like to trade on?"
    resp = inline_keyboard(dedent(speech))
    resp.add_button("Binance", "binance")
    resp.add_button("Bittrex", "bittrex")
    resp.add_button("Bitfinex", "bitfinex")
    resp.add_button("Poloniex", "poloniex")
    return resp


@assist.context("strat-config-data")
@assist.action("strat-config-exchange")
def prompt_quote_currency(exchange):
    context_manager.set("strat-config-data", "exchange", exchange)
    speech = f"""\
    Which currency would you like to use as the quote currency?
    This is the currency you will sell when making a buy order, and recieve when making a sell order.
    
    You must also allocate an amount of this currency to the strategy as capital base 
    This means you must hold the currency on {exchange} for live trading.
    """
    return ask(dedent(speech))


@assist.context("strat-config-data")
@assist.action("strat-config-quote-currency")
def prompt_capital_base(quote_currency):
    context_manager.set("strat-config-data", "quote_currency", quote_currency)
    speech = f"How much {quote_currency.upper()} would you like to allocate as the capital base?"
    return ask(speech)


@assist.context("strat-config-data")
@assist.action("strat-config-capital-base")
def prompt_trade_currency(capital_base):
    context_manager.set("strat-config-data", "captial_base", capital_base)
    speech = "Which asset would you like to trade?"
    return ask(speech)


@assist.context("strat-config-data")
@assist.action("strat-config-trade-currency")
def review_config(trade_currency):
    context_manager.set("strat-config-data", "trade_currency", trade_currency)
    context = context_manager.get("strat-config-data")

    strat = context.get("existing_strategy")
    exchange = context.get("exchange").title()
    base_currency = context.get("trade_currency").upper()
    quote_currency = context.get("quote_currency").upper()
    capital_base = context.get("capital_base")
    trade_pair = f"{base_currency}_{quote_currency}".lower()

    current_app.logger.error(strat)

    speech = """\
        Great, does this look right?

        Strategy: {}
        Exchange: {}
        Trade Pair: {}
        Capital Base: {} ({})
    """.format(
        strat, exchange, trade_pair, capital_base, quote_currency
    )

    return ask(dedent(speech)).with_quick_reply("yes", "no")


@assist.action("strat-config-confirm-yes")
def begin_mode_prompt():
    return event("strat-mode-start")


@assist.action("strat-mode", events=["strat-mode-start"])
def prompt_for_mode():
    context = context_manager.get("strat-config-data")
    backtest_id = utils.launch_backtest(context)

    current_app.logger.info(f"Queues Strat {backtest_id}")
    backtest_url = os.path.join(
        current_app.config["FRONTEND_URL"], "strategy/backtest/strategy/", backtest_id
    )

    speech = f"Your strategy is now configured!\n\n Would you like to launch it?\n\n Here’s a preview of how well this strategy performed over the past 3 days."

    resp = inline_keyboard(dedent(speech))
    resp.add_button("View Past Performance", url=backtest_url)
    resp.add_button("Launch in Paper Mode", "paper")
    resp.add_button("Lauch in Live mode", "live")
    resp.add_button("Nevermind", "no")

    return resp


@assist.context("strat-config-data")
@assist.action("strat-mode-paper")
def launch_strategy_paper(existing_strategy):
    context = context_manager.get("strat-config-data")
    job_id = utils.launch_paper(context)

    url = os.path.join(current_app.config["FRONTEND_URL"], "strategy/strategy/", job_id)

    speech = f"""\
    Great! The strategy is now running in paper mode and will run for the next 3 days.

    You can view your strategy's progress by clicking the link below and I will keep you updated on how it performs.
    """

    resp = inline_keyboard(dedent(speech))
    resp.add_button("View your Strategy", url=url)
    return resp


@assist.action("strat-mode-live")
def launch_strategy_paper(existing_strategy):
    context = context_manager.get("strat-config-data")
    job_id = utils.launch_live(context)

    url = os.path.join(current_app.config["FRONTEND_URL"], "strategy/strategy/", job_id)

    speech = f"""\
    Great! The strategy is now live and will run for the next 3 days.

    You can view your strategy's progress by clicking the link below and I will keep you updated on how it performs.
    """

    resp = inline_keyboard(dedent(speech))
    resp.add_button("View your Strategy", url=url)
    return resp




