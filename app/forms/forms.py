from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SelectField, IntegerField, FloatField, FieldList, FormField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Required, Optional
import talib as ta
from talib import abstract as ab

trade_types = [('backtest','backtest'), ('paper','paper'), ('live','live')]
exchanges = [('bitfinex', 'bitfinex'), ('poloniex', 'poloniex'), ('bittrex', 'bittrex')]
freqs = [('daily', 'daily'), ('minute', 'minute')]
datasets = [('None', 'None'), ('Google Trends, google'), ('Quandl Blochain Data', 'quandl')]



def indicator_group_name_selectors() -> [(str, str)]:
    """Returns list of select options of indicator group names"""
    selectors = []
    for k in ta.get_function_groups().keys():
        selectors.append((k, k))
    return selectors

def all_indicator_selectors() -> [(str, str)]:
    """Returns the entire list of possible indicator abbreviation select options"""
    selectors = []
    for i in ta.get_functions():
        selectors.append((i, i))
    return selectors


def _get_indicator_params(indicator_abbrev):
    func = getattr(ab, indicator_abbrev)
    return func.parameters


def get_indicators_by_group(group: str) -> [(str, str)]:
    """Returns list of select options containing abbreviations of the groups indicators"""
    indicator_selects = []
    group_indicators = ta.get_function_groups()[group]
    for i in range(len(group_indicators)):
        abbrev = group_indicators[i]
        func = getattr(ab, abbrev)
        name = func.info['display_name']
        indicator_selects.append((abbrev, abbrev))

    return indicator_selects


class UserExchangeKeysForm(FlaskForm):
    exchange = SelectField('Exchange', choices=exchanges, validators=[Required()], default=exchanges[0])
    api_key = StringField('API Key', validators=[DataRequired()])
    api_secret = PasswordField('API Secret', validators=[DataRequired()])
    submit = SubmitField('Authorize')



class TradeInfoForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    trade_type = SelectField('Trade Type', choices=trade_types, validators=[Required()], default=trade_types[0])
    start = StringField('Start', default="2017-10-10")
    end = StringField('End', default="2018-3-28")
    base_currency = StringField('Base Currency', default="usd")
    asset = StringField('Asset', default='btc_usd')
    data_freq = SelectField('Data Frequency', choices=freqs, validators = [Required()])
    history_freq = StringField('History frequency', default='1d')
    exchange = SelectField('Exchnage', choices=exchanges, validators=[Required()], default=exchanges[0])
    capital_base = IntegerField('Capital Base', validators=[DataRequired()], default=5000)
    bar_period = IntegerField('Bar Period', validators=[DataRequired()], default=50)
    order_size = FloatField('Order Size', validators=[DataRequired()], default=0.5)
    slippage_allowed = FloatField('Slippage Allowed', validators=[DataRequired()], default=0.05)
    submit = SubmitField('Next')


class DynamicChoiceField(SelectField):
    """An open ended select field to accept dynamic choices added by the browser"""

    def pre_validate(self, form):
        pass


class IndicatorInfoForm(FlaskForm):

    group = SelectField('Group', id='indicator_group_select')
    indicator_name = DynamicChoiceField('Indicator', validators=[], id='indicator_select')
    custom_label = StringField('Custom Indicator Label')
    symbol = StringField('Symbol')
    submit = SubmitField(label='Next')
    add = SubmitField(label='Add Another')
    # params are added dybnamically with js
