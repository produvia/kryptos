from flask import request, current_app
from app.models import User

EXISTING_STRATS = [
    # display, callback
    ('Bollinger Bands (BBANDS)', 'BBANDS'),
    ('Stop and Reverse (SAR)', 'SAR'),
    ('Moving Average Convergence/Divergence (MACD)', 'MACD'),
    ('Moving Average Convergence/Divergence Fix (MACDFIX)', 'MACDFIX'),
    ('On Balance Volume (OBV)', 'OBV'),
    ('Relative Strength Index (RSI)', 'RSI'),
    ('Stochastic (STOCH)', 'STOCH')
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
