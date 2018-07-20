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


