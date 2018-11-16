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


class DynamicChoiceField(SelectField):
    """An open ended select field to accept dynamic choices added by the browser"""

    def pre_validate(self, form):
        pass


class UserExchangeKeysForm(FlaskForm):
    exchange = SelectField(
        "Exchange",
        choices=build.EXCHANGES,
        validators=[Required()],
        default=build.EXCHANGES[0],
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
        choices=build.EXCHANGES,
        validators=[Required()],
        default=build.EXCHANGES[0],
        id="exchange_select",
    )

    quote_currency = DynamicChoiceField(
        "Quote Currency", id="quote_select", validators=[]
    )

    asset = DynamicChoiceField("Asset", id="asset_select", validators=[])

    capital_base = IntegerField("Capital Base", validators=[DataRequired()])
    trade_type = SelectField(
        "Trade Type",
        choices=build.TRADE_TYPES,
        validators=[Required()],
        default=build.TRADE_TYPES[0],
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

    strat_template = SelectField("Strategy", choices=build.EXISTING_STRATS)

    submit = SubmitField("Submit")
    # advanced = SubmitField("Advanced")


class AdvancedTradeInfoForm(_TradeInfoForm):

    data_freq = SelectField(
        "Data Frequency", choices=build.FREQS, validators=[Required()]
    )
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

    signal_type = SelectField("Signal Type", choices=build.SIGNAL_TYPES)
    target_series = SelectField("Target Indicator")
    func = SelectField(
        "Signal Function", choices=build.SIGNAL_FUNCS, id="signal-func-select"
    )

    # only one of the following will be active
    # depending on the func
    period = IntegerField("Period", id="signal-period-field", default=None)
    trigger_series = SelectField("Trigger", id="signal-trigger-field", default=None)
    submit = SubmitField("Submit")
    add_another = SubmitField(label="Add Another")
