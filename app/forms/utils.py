import talib as ta
from talib import abstract as ab

def indicator_group_name_selectors() -> [(str, str)]:
    """Returns list of select options of indicator group names"""
    selectors = []
    for k in ta.get_function_groups().keys():
        selectors.append((k, k))
    return selectors

def all_indicator_selectors() -> [(str, str)]:
    """Returns the entire list of possible indicator abbreviation select options"""
    selectors = []
    for i in ta.get_functions():
        selectors.append((i, i))
    return selectors


def _get_indicator_params(indicator_abbrev):
    func = getattr(ab, indicator_abbrev)
    return func.parameters


def get_indicators_by_group(group: str) -> [(str, str)]:
    """Returns list of select options containing abbreviations of the groups indicators"""
    indicator_selects = []
    group_indicators = ta.get_function_groups()[group]
    for i in range(len(group_indicators)):
        abbrev = group_indicators[i]
        func = getattr(ab, abbrev)
        name = func.info['display_name']
        indicator_selects.append((abbrev, abbrev))

    return indicator_selects

def process_trading_form(form):
    trading_dict = {
       "EXCHANGE": form.exchange.data,
       "ASSET": form.asset.data,
       "DATA_FREQ": form.data_freq.data,
       "HISTORY_FREQ": form.history_freq.data,
       "CAPITAL_BASE": form.capital_base.data,
       "BASE_CURRENCY": form.base_currency.data,
       "START": form.start.data,
       "END": form.end.data,
       "BARS": form.bar_period.data,
       "ORDER_SIZE": form.order_size.data,
       "SLIPPAGE_ALLOWED": form.slippage_allowed.data

    }
    return trading_dict

def process_indicator_form(form):
    indicator_dict = {
        'name': form.indicator_name.data,
        'symbol': form.symbol.data,
        'label': form.custom_label.data
    }
    return indicator_dict

def process_signal_form(form):
    signal_dict = {}
    signal_dict['func'] = form.func.data
    signal_dict['params'] = {}
    signal_dict['params']['series'] = form.target_series.data

    if form.period.data is not None:
        signal_dict['params']['period'] = form.period.data
    else:
        signal_dict['params']['trigger'] = form.trigger_series.data

    return signal_dict
