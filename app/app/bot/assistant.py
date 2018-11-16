import logging
import os
from textwrap import dedent

from flask import Blueprint, current_app
from flask_assistant import Assistant, tell, event, context_manager

from app.bot.response import ask, inline_keyboard
from app.utils import build
from app import task

blueprint = Blueprint("bot", __name__, url_prefix="/bot")
assist = Assistant(blueprint=blueprint)


logging.getLogger("flask_assistant").setLevel(logging.INFO)


@assist.action("Default Welcome Intent")
def welcome_message():
    user_name = build.get_first_name()
    msg = f"Hello {user_name}!"
    msg += """I’m Kryptos AI, your virtual investment assistant\
    that manages your cryptocurrency portfolio and automate\
    your cryptocurrency trading"""

    if build.get_user() is None:
        current_app.logger.info("Prompting user to login")
        msg += """\n\n \
        Before we can get started,you'll need to \
        create a free Kryptos account and authentiate with Telegram
        """
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
    user = build.get_user()
    user.unlink_telegram()
    speech = f"""\
    Your account is now unlinked
    You can always re-link at {current_app.config['FRONTEND_URL']}
    """
    return tell(dedent(speech))


@assist.action("activity-menu")
def show_menu():
    user_name = build.get_first_name()
    resp = inline_keyboard(f"Hi {user_name}. Let's get started")
    resp.add_button("new_strat", "Launch New Strategy")
    resp.add_button("performance_report", "Run performance report")
    resp.add_button("update_goals", "Update Goals")
    resp.add_button("upgrade_skills", "Upgrade Skills")
    resp.add_button("adjust_keytpos", "Adjust Kryptos")

    return resp


# TODO get group indicators from rq
# @assist.action("new-strategy-display-momentum")
# def display_momentum_indicators():
#     momentum_indicators = ta.get_function_groups()["Momentum Indicators"]
#     speech = "Here are all the possible Momentum Indicators you can use:"
#     for i in range(len(momentum_indicators)):
#         abbrev = momentum_indicators[i]

#         func = getattr(ab, abbrev)
#         name = func.info["display_name"]
#         speech += f"\n{i+1}. {abbrev} - {name}"
#     return ask(speech)


#########################
# BUILD STRATEGY CONFIG #
#########################


@assist.action("new-strategy")
def display_available_strats():
    context_manager.add("strat-config-data")
    resp = inline_keyboard("Which strategy do you wish to try?")
    for i in build.EXISTING_STRATS:
        resp.add_button(*i)
    return resp


@assist.context("strat-config-data")
@assist.action("new-strategy-select-strat")
def select_strategy(existing_strategy):
    return event("strat-config-start", existing_strategy=existing_strategy)


@assist.context("strat-config-data")
@assist.action("strat-config", events=["strat-config-start"])
def prompt_exchange(existing_strategy):
    current_app.logger.debug(f"Building strategy for {existing_strategy}")
    context_manager.set("strat-config-data", "existing_strategy", existing_strategy)
    speech = "Which exchange would you like to trade on?"
    resp = inline_keyboard(dedent(speech))
    for e in build.EXCHANGES:
        resp.add_button(*e)
        current_app.logger.debug("Engqueuing exchange option jobs")
        # enqueue job to be ready when needed
        task.get_exchange_asset_pairs(e[1])
        task.get_exchange_quote_currencies(e[1])

    return resp


@assist.context("strat-config-data")
@assist.action("strat-config-exchange")
def prompt_quote_currency(exchange):
    current_app.logger.debug(f"Setting exchange as {exchange}")
    context_manager.set("strat-config-data", "exchange", exchange)
    speech = f"""\
    Which currency would you like to use as the quote currency?
    This is the currency you will sell when making a buy order, and recieve when making a sell order.

    You must also allocate an amount of this currency to the strategy as capital base
    This means you must hold the currency on {exchange} for live trading.
    """
    resp = inline_keyboard(dedent(speech))
    quotes = task.get_exchange_quote_currencies(exchange)

    for q in quotes:
        resp.add_button(q.lower(), q)
    return resp


@assist.context("strat-config-data")
@assist.action("strat-config-quote-currency")
def prompt_capital_base(quote_currency):
    current_app.logger.debug(f"Setting quote currency as {quote_currency}")
    context_manager.set("strat-config-data", "quote_currency", quote_currency)
    speech = f"How much {quote_currency.upper()} would you like to allocate as the capital base?"

    exchange = context_manager.get("strat-config-data").get("exchange")
    # enqueue base_currency options
    current_app.logger.debug("enqueing for base currencies")
    task.get_available_base_currencies(exchange, quote_currency)
    return ask(speech)


@assist.context("strat-config-data")
@assist.action("strat-config-capital-base")
def prompt_trade_currency(capital_base):
    current_app.logger.debug(f"Setting capital base as {capital_base}")
    context_manager.set("strat-config-data", "captial_base", capital_base)

    speech = "Which asset would you like to trade?"
    resp = inline_keyboard(speech)

    exchange = context_manager.get("strat-config-data").get("exchange")
    quote_currency = context_manager.get("strat-config-data").get("quote_currency")

    options = task.get_available_base_currencies(exchange, quote_currency)

    for o in options:
        resp.add_button(o, o)
    return resp


@assist.context("strat-config-data")
@assist.action("strat-config-trade-currency")
def prompt_for_hours(trade_currency):
    current_app.logger.debug(f"Setting trade currency as {trade_currency}")
    context_manager.set("strat-config-data", "trade_currency", trade_currency)

    speech = "For how many hours would you like the run the strategy?"
    return ask(speech)


@assist.context("strat-config-data")
@assist.action("strat-config-hours")
def review_config(hours):
    current_app.logger.debug(f"Setting hours as {hours}")
    context_manager.set("strat-config-data", "hours", hours)
    context = context_manager.get("strat-config-data")

    strat = context.get("existing_strategy")
    exchange = context.get("exchange").title()
    base_currency = context.get("trade_currency").upper()
    quote_currency = context.get("quote_currency").upper()
    capital_base = context.get("capital_base")
    trade_pair = f"{base_currency}_{quote_currency}".lower()

    speech = """\
        Great, does this look right?

        Strategy: {}
        Exchange: {}
        Trade Pair: {}
        Capital Base: {} ({})
        Run for: {} hours
    """.format(
        strat, exchange, trade_pair, capital_base, quote_currency, hours
    )

    return ask(dedent(speech)).with_quick_reply("yes", "no")


@assist.action("strat-config-confirm-yes")
def begin_mode_prompt():
    return event("strat-mode-start")


@assist.action("strat-mode", events=["strat-mode-start"])
def prompt_for_mode():
    context = context_manager.get("strat-config-data")
    # backtest_id = build.launch_backtest(context)

    # current_app.logger.info(f"Queues Strat {backtest_id}")
    # backtest_url = os.path.join(
    #     current_app.config["FRONTEND_URL"], "strategy/backtest/strategy/", backtest_id
    # )

    speech = f"Your strategy is now configured!\n\n Would you like to launch it?\n\n"

    resp = inline_keyboard(dedent(speech))
    # resp.add_button("View Past Performance", url=backtest_url)
    resp.add_button("paper", "Launch in Paper Mode")
    resp.add_button("live", "Lauch in Live mode")
    resp.add_button("no", "Nevermind")

    return resp


@assist.context("strat-config-data")
@assist.action("strat-mode-paper")
def launch_strategy_paper(existing_strategy):
    context = context_manager.get("strat-config-data")
    job_id = build.launch_paper(context)

    url = os.path.join(current_app.config["FRONTEND_URL"], "strategy", job_id)

    hours = context.get("hours")
    speech = """\
    Great! The strategy is now running in paper mode \
    and will run for the next {} hours.

    You can view your strategy's progress by clicking the link \
    below and I will keep you updated on how it performs.
    """.format(
        hours
    )

    resp = inline_keyboard(dedent(speech))
    resp.add_link(url, "View your Strategy")
    return resp


@assist.action("strat-mode-live")
def launch_strategy_live(existing_strategy):
    context = context_manager.get("strat-config-data")
    job_id = build.launch_live(context)

    url = os.path.join(current_app.config["FRONTEND_URL"], "strategy", job_id)

    hours = context.get("hours")
    speech = f"""\
    Great! The strategy is now live and will run for the next {hours} hours.

    You can view your strategy's progress by clicking the link \
    below and I will keep you updated on how it performs.
    """.format(
        hours
    )

    resp = inline_keyboard(dedent(speech))
    resp.add_button(url, "View your Strategy")
    return resp
