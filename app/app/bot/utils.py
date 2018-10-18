import datetime
import json
from flask import request, current_app
import ccxt

from app.models import User
from app import task

EXISTING_STRATS = [
    # display, callback
    ("Bollinger Bands (BBANDS)", "BBANDS"),
    ("Stop and Reverse (SAR)", "SAR"),
    ("Moving Average Convergence/Divergence (MACD)", "MACD"),
    ("Moving Average Convergence/Divergence Fix (MACDFIX)", "MACDFIX"),
    ("On Balance Volume (OBV)", "OBV"),
    ("Relative Strength Index (RSI)", "RSI"),
    ("Stochastic (STOCH)", "STOCH"),
]

# TODO possibly use telegram chat_id
def get_user():
    telegram_id = get_message_payload()["id"]
    user = User.query.filter_by(telegram_id=telegram_id).first()
    current_app.logger.debug(f"Got user {user}")
    return user


def get_first_name():
    name = get_message_payload().get("first_name", None)
    if name is not None:
        return name
    return ""


def get_message_payload():
    platform_data = request.json.get("originalRequest", {}).get("data", {})
    current_app.logger.info(platform_data)
    if not platform_data:
        return {"first_name": "DialogFlow", "id": 111}

    if platform_data.get("message"):
        return platform_data["message"]["from"]

    elif platform_data.get("callback_query"):
        return platform_data["callback_query"]["from"]


def get_exchange_pairs(exchange_name: str):
    current_app.logger.debug(f"Fetching {exchange_name} markets with ccxt")
    exchange_class = getattr(ccxt, exchange_name)
    markets = exchange_class().load_markets()
    symbols = []
    for pair in markets:
        s = pair.replace("/", "_").lower()
        symbols.append(s)
    return symbols


def build_strat_dict_from_context(context, mode):
    strat = context.get("existing_strategy")
    exchange = context.get("exchange").title()
    base_currency = context.get("trade_currency").upper()
    quote_currency = context.get("quote_currency").upper()
    capital_base = context.get("capital_base")
    trade_pair = f"{base_currency}_{quote_currency}".lower()

    start = datetime.datetime.today()
    end = start + datetime.timedelta(days=3)

    strat_dict = {"trading": {}, "indicators": [{"name": strat}]}
    strat_dict["trading"]["START"] = datetime.datetime.strftime(start, "%Y-%m-%d")
    strat_dict["trading"]["END"] = datetime.datetime.strftime(end, "%Y-%m-%d")

    strat_dict["trading"]["EXCHANGE"] = exchange
    strat_dict["trading"]["ASSET"] = trade_pair
    strat_dict["trading"]["CAPITAL_BASE"] = float(capital_base)
    strat_dict["trading"]["BASE_CURRENCY"] = quote_currency  # TODO change refs of base to quote

    strat_dict["name"] = f"{strat}-{mode.title()}"
    return strat_dict


def build_strat_dict(strategy_name, mode):
    start = datetime.datetime.today()
    end = start + datetime.timedelta(days=3)

    strat_dict = {"trading": {}, "indicators": [{"name": strategy_name}]}
    strat_dict["trading"]["START"] = datetime.datetime.strftime(start, "%Y-%m-%d")
    strat_dict["trading"]["END"] = datetime.datetime.strftime(end, "%Y-%m-%d")
    strat_dict["name"] = f"{strategy_name}-{mode.title()}"
    return strat_dict


def launch_backtest(config_context):
    strat_dict = build_strat_dict_from_context(config_context, "backtest")

    # Can't use today as the end date bc data bundles are updated daily,
    # so current market data won't be avialable for backtest until the following day
    # use past week up to yesterday
    back_start = datetime.datetime.today() - datetime.timedelta(days=4)
    back_end = datetime.datetime.today() - datetime.timedelta(days=1)

    strat_dict["trading"]["START"] = datetime.datetime.strftime(back_start, "%Y-%m-%d")
    strat_dict["trading"]["END"] = datetime.datetime.strftime(back_end, "%Y-%m-%d")

    backtest_id, _ = task.queue_strat(
        json.dumps(strat_dict), user_id=None, live=False, simulate_orders=True
    )
    return backtest_id


def launch_paper(config_context):
    user = get_user()
    strat_dict = build_strat_dict_from_context(config_context, "paper")
    job_id, _ = task.queue_strat(json.dumps(strat_dict), user.id, live=True, simulate_orders=True)

    return job_id


def launch_live(config_context):
    user = get_user()
    strat_dict = build_strat_dict_from_context(config_context, "live")
    job_id, _ = task.queue_strat(json.dumps(strat_dict), user.id, live=True, simulate_orders=False)
    return job_id
