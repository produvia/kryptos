from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SelectField, IntegerField, FloatField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Required

trade_types = [('backtest','backtest'), ('paper','paper'), ('live','live')]
exchanges = [('bitfinex', 'bitfinex'), ('poloniex', 'poloniex'), ('bittrex', 'bittrex')]
freqs = [('daily', 'daily'), ('minute', 'minute')]




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
    submit = SubmitField('Submit')
