from crypto_platform.config import CONFIG

MA_TYPE_MAP = {
    'SMA': 0,    # Simple Moving Average
    'EMA': 1,    # Exponential Moving Average
    'WMA': 2,    # Weighted Moving Average
    'DEMA': 3,   # Double Exponential Moving Average
    'TEMA': 4,   # Triple Exponential Moving Average
    'TRIMA': 5,  # Triangular Moving Average
    'KAMA': 6,   # Kaufman Adaptive Moving Average
    'MAMA': 7,   # MESA Adaptive Moving Average
    'T3': 8,     # Triple Generalized Double Exponential Moving Average
}


class AbstractIndicator(object):
    def __init__(self, name, label=None, symbol=CONFIG.ASSET, dataset=None, **kw):
        """Abstract class defining required methods utilized by Strategy objects"""

        self.name = name.upper()
        self.label = label or self.name
        self.symbol = symbol
        self.dataset = dataset

        self.params = {}
        self.available_params = []

        func_params = kw.get('params', {})
        self._parse_params(func_params)

        self.data = None
        self.outputs = None

    def serialize(self):
        d = {
            "name": self.name,
            "symbol": self.symbol,
            "dataset": self.dataset,
            "label": self.label,
            "params": self.params
        }
        return d

    def _parse_params(self, func_params):
        for k, v in func_params.items():
            if k == 'matype' and isinstance(v, str):
                v = MA_TYPE_MAP[v]
            self.params[k] = v


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
