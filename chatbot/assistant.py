import logging
from textwrap import dedent
from flask import Flask, request
from flask_assistant import Assistant, ask, tell, event, context_manager
from flask_assistant.response import _Response
import talib as ta
import talib.abstract as ab


app = Flask(__name__)
assist = Assistant(app)
logging.getLogger('flask_assistant').setLevel(logging.DEBUG)

class ask(_Response):
    def __init__(self, speech, display_text=None):
        """Returns a response to the user and keeps the current session alive. Expects a response from the user.
        Arguments:
            speech {str} --  Text to be pronounced to the user / shown on the screen
        """
        super(ask, self).__init__(speech, display_text)
        self._response['data']['google']['expect_user_response'] = True

    def reprompt(self, prompt):
        self._response['data']['google'][
            'no_input_prompts'] = [{'text_to_speech': prompt}]

        return self

    def with_quick_reply(self, *options, text=None):
        if text is None:
            text = self._speech
        msg = {
            'type': 2,
            'platform': 'telegram',
            'title': text,
            'replies': options
        }
        self._response['messages'].append(msg)
        return self

def get_user_from_request():
    if not request.json.get('originalRequest'):
        return {'first_name': 'USER', 'id': 34567}
    return request.json['originalRequest']['data']['message']['from']


@assist.action('activity-menu')
def show_menu():
    user_name = get_user_from_request()['first_name']
    speech = f"""\
    Hi {user_name}. Let's get started. Please select a number or text me the named
    1. Launch New Strategy
    2. Run Performance Report
    3. Update Goals
    4. Upgrade SKills
    5 Adjust Kryptos"""
    return ask(speech).with_quick_reply('1', '2', '3', '4', '5')


# @assist.context('activity-selection')
@assist.action('new-strategy')
def display_available_strats():
    speech = """\
    Great. Which strategy do you wish to try?
    1. Simple Moving Average (SMA) Crossover
    2. Relative Strength Index (RSI)
    3. Explore Momentum Indicators
    """
    return ask(dedent(speech)).with_quick_reply('1', '2', '3')

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


if __name__ == '__main__':
    app.run(debug=True)
