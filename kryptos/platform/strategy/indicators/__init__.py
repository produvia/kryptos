import logbook

from kryptos.platform import logger_group
from kryptos.platform.strategy import DEFAULT_CONFIG


MA_TYPE_MAP = {
    "SMA": 0,  # Simple Moving Average
    "EMA": 1,  # Exponential Moving Average
    "WMA": 2,  # Weighted Moving Average
    "DEMA": 3,  # Double Exponential Moving Average
    "TEMA": 4,  # Triple Exponential Moving Average
    "TRIMA": 5,  # Triangular Moving Average
    "KAMA": 6,  # Kaufman Adaptive Moving Average
    "MAMA": 7,  # MESA Adaptive Moving Average
    "T3": 8,  # Triple Generalized Double Exponential Moving Average
}


class IndicatorLogger(logbook.Logger):

    def __init__(self, indicator):
        self.indicator = indicator
        super().__init__(name="INDICATOR:{}".format(self.indicator.name))

    def process_record(self, record):
        logbook.Logger.process_record(self, record)
        record.extra["trade_date"] = self.indicator.current_date
        record.extra["ind_data"] = self.indicator.data
        record.extra["ind_outputs"] = self.indicator.outputs


class AbstractIndicator(object):

    def __init__(self, name, label=None, symbol=None, dataset=None, **kw):
        """Abstract class defining required methods utilized by Strategy objects"""

        self.name = name.upper()
        self.label = label or self.name
        self.symbol = symbol or DEFAULT_CONFIG["ASSET"]
        self.dataset = dataset

        self.params = {}

        func_params = kw.get("params", {})
        self._parse_params(func_params)

        self.data = None
        self.outputs = None
        self.current_date = None
        self.result = None
        self.results_pred = []
        self.results_real = []
        self.idx = -1
        self.hyper_params = None
        self.num_boost_rounds = None

        self.log = IndicatorLogger(self)
        logger_group.add_logger(self.log)
        self.log.info("Attached {} indicator".format(self.name))

    @property
    def default_params(self):
        return {}

    def update_param(self, param, val):
        self._parse_params({param: val})

    def serialize(self):
        d = {
            "name": self.name,
            "symbol": self.symbol,
            "dataset": self.dataset,
            "label": self.label,
            "params": self.params,
        }
        return d

    def _parse_params(self, func_params):
        self.params.update(self.default_params)
        for k, v in func_params.items():
            if "matype" in k and isinstance(v, str):
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
