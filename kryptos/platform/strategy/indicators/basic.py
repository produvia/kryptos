from catalyst.api import record
from logbook import Logger

from kryptos.platform.utils import viz
from kryptos.platform.strategy.indicators import AbstractIndicator
from kryptos.platform import logger_group

log = Logger("BasicIndicator")
logger_group.add_logger(log)


def get_indicator(name, **kw):
    subclass = globals().get(name.upper())
    if subclass is not None:
        return subclass(**kw)

    raise LookupError("No dataset found with name {}".format(name))


class RELCHANGE(AbstractIndicator):

    def __init__(self, delta_t=4, **kw):
        super().__init__("RELCHANGE", delta_t=delta_t, **kw)
        self.delta_t = delta_t

    def calculate(self, trend_series):
        self.data = trend_series

        df = trend_series.to_frame(name="val")
        df["mean"] = df["val"].rolling(self.delta_t).mean()

        df["rel_change"] = df["val"] - df["mean"].shift(periods=1, freq=self.delta_t)
        df["rel_change_ratio"] = df["rel_change"] / df["mean"].shift(periods=1, freq=self.delta_t)

        self.outputs = df.fillna(value=0)

    @property
    def default_params(self):
        return {}

    def record(self):
        record(
            rel_change=self.outputs.rel_change[-1],
            rel_change_ratio=self.outputs.rel_change_ratio[-1],
        )

    def plot(self, results, pos, **kw):
        ax = viz.plot_column(results, "rel_change", pos, label="Relative Change", color="r", **kw)
        ax2 = viz.plot_column(
            results,
            "rel_change_ratio",
            pos,
            label="Relative Change Ratio",
            color="g",
            twin=ax,
            **kw
        )

        viz.add_twin_legends([ax, ax2])

    @property
    def signals_sell(self):
        try:
            return self.outputs.rel_change[-1] < 0.0

        except AttributeError as e:
            self.log.exception(e)
            return False

    @property
    def signals_buy(self):
        try:
            return self.outputs.rel_change[-1] > 0.0

        except AttributeError as e:
            self.log.exception(e)
            return False
