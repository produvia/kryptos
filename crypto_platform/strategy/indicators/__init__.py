class Indicator(object):
    """Base class for Indicator objects"""

    def __init__(self):
        self.prices = None

    def calculate(self, prices):
        raise NotImplementedError

    def record(self):
        raise NotImplementedError

    def plot(self):
        raise NotImplementedError

    @property
    def current_price(self):
        return self.prices.close[-1]

    @property
    def signals_buy(self):
        raise NotImplementedError

    @property
    def signals_sell(self):
        raise NotImplementedError

    def set_signal_threshold(self, *args, **kwargs):
        raise NotImplementedError