import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateTimeField,
    SelectField,
    IntegerField,
    FloatField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import DataRequired, Required
from app.utils import build

trade_types = [("paper", "paper"), ("live", "live"), ("backtest", "backtest")]
exchanges = [
    ("binance", "binance"),
    ("bitfinex", "bitfinex"),
    ("poloniex", "poloniex"),
    ("bittrex", "bittrex"),
]
existing_strats = [
    ("BBANDS", "Bollinger Bands (BBANDS)"),
    ("SAR", "Stop and Reverse (SAR)"),
    ("MACD", "Moving Average Convergence/Divergence (MACD)"),
    ("MACDFIX", "Moving Average Convergence/Divergence Fix (MACDFIX)"),
    ("OBV", "On Balance Volume (OBV)"),
    ("RSI", "Relative Strength Index (RSI)"),
    ("STOCH", "Stochastic (STOCH)"),
    ("XGBOOST", "XGBOOST (ML)"),
    ("LIGHTGBM", "LIGHTGBM (ML)"),
]


freqs = [("daily", "daily"), ("minute", "minute")]
datasets = [
    ("None", "None"),
    ("Google Trends, google"),
    ("Quandl Blochain Data", "quandl"),
]

signal_types = [("buy", "Buy"), ("sell", "Sell")]


signal_funcs = [
    ("decreasing", "Decreasing for"),
    ("increasing", "Increasing for"),
    ("cross_above", "Crosses Above"),
    ("cross_below", "Crosses Below"),
]


class DynamicChoiceField(SelectField):
    """An open ended select field to accept dynamic choices added by the browser"""

    def pre_validate(self, form):
        pass


class UserExchangeKeysForm(FlaskForm):
    exchange = SelectField(
        "Exchange", choices=exchanges, validators=[Required()], default=exchanges[0]
    )
    api_key = StringField("API Key", validators=[DataRequired()])
    api_secret = PasswordField("API Secret", validators=[DataRequired()])
    submit = SubmitField("Authorize")


class UserExchangeKeyRemoveForm(FlaskForm):
    exchange_name = SelectField("Choose to remove")
    remove = SubmitField("Remove")


class _TradeInfoForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])

    exchange = SelectField(
        "Exchange",
        choices=exchanges,
        validators=[Required()],
        default=exchanges[0],
        id="exchange_select",
    )

    asset = DynamicChoiceField("Asset", id="asset_select", validators=[])

    quote_currency = StringField("Quote Currency", id="quote_select", validators=[])
    capital_base = IntegerField("Capital Base", validators=[DataRequired()])

    trade_type = SelectField(
        "Trade Type",
        choices=trade_types,
        validators=[Required()],
        default=trade_types[0],
    )

    start = DateTimeField(
        "Start", default=datetime.datetime.utcnow(), format="%Y-%m-%d %I:%M %p"
    )

    end = DateTimeField(
        "End",
        default=(datetime.datetime.utcnow() + datetime.timedelta(days=1)),
        format="%Y-%m-%d %I:%M %p",
    )


class BasicTradeInfoForm(_TradeInfoForm):

    strat_template = SelectField("Strategy", choices=existing_strats)

    submit = SubmitField("Submit")
    # advanced = SubmitField("Advanced")


class AdvancedTradeInfoForm(_TradeInfoForm):

    data_freq = SelectField("Data Frequency", choices=freqs, validators=[Required()])
    history_freq = StringField("History frequency", default="1d")

    bar_period = IntegerField("Bar Period", validators=[DataRequired()], default=50)
    order_size = FloatField("Order Size", validators=[DataRequired()], default=0.5)
    slippage_allowed = FloatField(
        "Slippage Allowed", validators=[DataRequired()], default=0.05
    )
    next_step = SubmitField("Next")


class IndicatorInfoForm(FlaskForm):

    group = SelectField("Group", id="indicator_group_select")
    indicator_name = DynamicChoiceField(
        "Indicator", validators=[], id="indicator_select"
    )
    custom_label = StringField("Custom Indicator Label")
    symbol = StringField("Symbol")
    next_step = SubmitField(label="Next")
    add_another = SubmitField(label="Add Another")
    # params are added dybnamically with js


class SignalForm(FlaskForm):

    signal_type = SelectField("Signal Type", choices=signal_types)
    target_series = SelectField("Target Indicator")
    func = SelectField("Signal Function", choices=signal_funcs, id="signal-func-select")

    # only one of the following will be active
    # depending on the func
    period = IntegerField("Period", id="signal-period-field", default=None)
    trigger_series = SelectField("Trigger", id="signal-trigger-field", default=None)
    submit = SubmitField("Submit")
    add_another = SubmitField(label="Add Another")
