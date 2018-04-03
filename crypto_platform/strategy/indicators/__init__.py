class AbstractIndicator(object):
    def __init__(self, name, symbol=None, period_length=None, min_history_period=None, num_periods=None, **kw):
        """Abstract class defining required methods utilized by Strategy objects"""
        self.name = name.upper()
        self.data = None
        self.outputs = None

    def calculate(self, df):
        raise NotImplementedError

    def record(self):
        raise NotImplementedError

    def plot(self, results, pos, *kw):
        raise NotImplementedError

    @property
    def signals_buy(self):
        raise NotImplementedError

    @property
    def signals_sell(self):
        raise NotImplementedError

    def set_signal_threshold(self, *args, **kwargs):
        raise NotImplementedError
