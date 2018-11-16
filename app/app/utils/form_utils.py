from flask import current_app
import datetime
from app.utils import choices


def process_trading_form(form):
    trading_dict = {
        "EXCHANGE": form.exchange.data,
        "ASSET": form.asset.data,
        "CAPITAL_BASE": form.capital_base.data,
        "QUOTE_CURRENCY": form.quote_currency.data,
        "START": form.start.data,
        "END": form.end.data,
        # the following are not provided in the basic form
        "DATA_FREQ": form.data.get("data_freq"),
        "HISTORY_FREQ": form.data.get("history_freq"),
        "BARS": form.data.get("bar_period"),
        "ORDER_SIZE": form.data.get("order_size"),
        "SLIPPAGE_ALLOWED": form.data.get("slippage_allowed"),
    }

    # remove None vals so strat will use defaults
    return {k: v for k, v in trading_dict.items() if v is not None}


def build_strat_dict_from_form(form):
    current_app.logger.info(form.data)

    trading_dict = process_trading_form(form)

    trading_dict["START"] = datetime.datetime.strftime(
        form.start.data, "%Y-%m-%d %H:%M"
    )
    trading_dict["END"] = datetime.datetime.strftime(form.end.data, "%Y-%m-%d %H:%M")

    strat_dict = {"name": form.name.data, "trading": trading_dict}

    strat_tmpl = form.strat_template.data
    if strat_tmpl in choices.ML_MODELS:
        strat_dict["models"] = [{"name": strat_tmpl}]
    else:
        strat_dict["inidicators"] = [{"name": strat_tmpl}]

    current_app.logger.info("Built reading dict")
    current_app.logger.info(strat_dict)

    return strat_dict


def process_indicator_form(form):
    indicator_dict = {
        "name": form.indicator_name.data,
        "symbol": form.symbol.data,
        "label": form.custom_label.data,
    }
    return indicator_dict


def process_signal_form(form):
    signal_dict = {}
    signal_dict["func"] = form.func.data
    signal_dict["params"] = {}
    signal_dict["params"]["series"] = form.target_series.data

    if form.period.data is not None:
        signal_dict["params"]["period"] = form.period.data
    else:
        signal_dict["params"]["trigger"] = form.trigger_series.data

    return signal_dict
