from flask_assistant import ask
from flask_assistant.response import _Response


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


class inline_keyboard(ask):

    def __init__(self, msg, buttons=None):
        super().__init__(speech=msg)

        if buttons is None:
            buttons = []

        self._buttons = buttons


    def render_response(self):
        self._response['messages'].append(self._custom_msg)
        return super().render_response()

    @property
    def _custom_msg(self):
        return {
          "type": 4,
          "platform": "telegram",
          "payload": self._payload,
        }



    @property
    def _payload(self):
        return {
           "telegram":{
              "text": self._speech,
              "reply_markup": {
                 "inline_keyboard": self._buttons
              }
           }
        }


    def add_button(self, text, callback_data=None, url=None):
        if None not in [callback_data, url]:
            raise ValueError('Buttons may only include one of callback_data or url')
        btn = {
           "text": text,
           "callback_data": callback_data,
           "url": url
        }
        btn_row = [btn] # inline keybaord accepts array of button row arrays
        self._buttons.append(btn_row)