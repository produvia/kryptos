class Indicator(object):
    """Base class for Indicator objects"""

    def __init__(self):
        self.values = None

    def calculate(self, values):
        raise NotImplementedError

    def record(self):
        raise NotImplementedError

    def plot(self):
        raise NotImplementedError

    @property
    def signals_buy(self):
        raise NotImplementedError

    @property
    def signals_sell(self):
        raise NotImplementedError

    def set_signal_threshold(self, *args, **kwargs):
        raise NotImplementedError
