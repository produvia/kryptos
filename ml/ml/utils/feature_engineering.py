import os
import numpy as np
import pandas as pd
import talib as ta
from datetime import datetime
from ta import add_all_ta_features
#from tsfresh import extract_features, extract_relevant_features
#from tsfresh.utilities.dataframe_functions import roll_time_series
from fbprophet import Prophet

def add_utils_features(df):
    """Add utils features.

    Args:
        df(pandas.DataFrame): original DataFrame.
        timestamp(pandas.tslib.Timestamp): timestamp.
    Returns:
        pandas.DataFrame: DataFrame with new dates features included.
    """
    df['utils_counter'] = np.array(range(1, df.shape[0] + 1))

    return df


def add_dates_features(df):
    """Add dates features.

    Args:
        df(pandas.DataFrame): original DataFrame.
    Returns:
        pandas.DataFrame: DataFrame with new dates features included.
    """
    df['date_year'] = df.timestamp.dt.year
    df['date_month'] = df.timestamp.dt.month
    df['date_weekofyear'] = df.timestamp.dt.weekofyear
    df['date_week'] = df.timestamp.dt.week
    df['date_weekday'] = df.timestamp.dt.weekday
    df['date_day'] = df.timestamp.dt.day
    # TODO: only if minute frequency:
    df['date_hour'] = df.timestamp.dt.hour
    df['date_minute'] = df.timestamp.dt.minute
    return df


def add_ta_features2(df, ta_settings):
    """Add technial analysis features from typical financial dataset that
    typically include columns such as "open", "high", "low", "price" and
    "volume".

    http://github.com/bukosabino/ta

    Args:
        df(pandas.DataFrame): original DataFrame.
        ta_settings(dict): configuration.
    Returns:
        pandas.DataFrame: DataFrame with new features included.
    """

    if ta_settings:
        # Add ta features filling NaN values
        df = add_all_ta_features(df, "open", "high", "low", "price", "volume",
                                    fillna=True)

    return df


def add_ta_features(df, ta_settings):
    """Add technial analysis features from typical financial dataset that
    typically include columns such as "open", "high", "low", "price" and
    "volume".

    http://mrjbq7.github.io/ta-lib/

    Args:
        df(pandas.DataFrame): original DataFrame.
        ta_settings(dict): configuration.
    Returns:
        pandas.DataFrame: DataFrame with new features included.
    """

    open = df['open']
    high = df['high']
    low = df['low']
    close = df['price']
    volume = df['volume']

    if ta_settings['overlap']:

        df['ta_overlap_bbands_upper'], df['ta_overlap_bbands_middle'], df['ta_overlap_bbands_lower'] = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        df['ta_overlap_dema'] = ta.DEMA(close, timeperiod=15) # NOTE: Changed to avoid a lot of Nan values
        df['ta_overlap_ema'] = ta.EMA(close, timeperiod=30)
        df['ta_overlap_kama'] = ta.KAMA(close, timeperiod=30)
        df['ta_overlap_ma'] = ta.MA(close, timeperiod=30, matype=0)
        df['ta_overlap_mama_mama'], df['ta_overlap_mama_fama'] = ta.MAMA(close)
        period = np.random.randint(10, 20, size=len(close)).astype(float)
        df['ta_overlap_mavp'] = ta.MAVP(close, period, minperiod=2, maxperiod=30, matype=0)
        df['ta_overlap_midpoint'] = ta.MIDPOINT(close, timeperiod=14)
        df['ta_overlap_midprice'] = ta.MIDPRICE(high, low, timeperiod=14)
        df['ta_overlap_sar'] = ta.SAR(high, low, acceleration=0, maximum=0)
        df['ta_overlap_sarext'] = ta.SAREXT(high, low, startvalue=0, offsetonreverse=0, accelerationinitlong=0, accelerationlong=0, accelerationmaxlong=0, accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0)
        df['ta_overlap_sma'] = ta.SMA(close, timeperiod=30)
        df['ta_overlap_t3'] = ta.T3(close, timeperiod=5, vfactor=0)
        df['ta_overlap_tema'] = ta.TEMA(close, timeperiod=12) # NOTE: Changed to avoid a lot of Nan values
        df['ta_overlap_trima'] = ta.TRIMA(close, timeperiod=30)
        df['ta_overlap_wma'] = ta.WMA(close, timeperiod=30)

        # NOTE: Commented to avoid a lot of Nan values
        # df['ta_overlap_ht_trendline'] = ta.HT_TRENDLINE(close)

    if ta_settings['momentum']:

        df['ta_momentum_adx'] = ta.ADX(high, low, close, timeperiod=14)
        df['ta_momentum_adxr'] = ta.ADXR(high, low, close, timeperiod=14)
        df['ta_momentum_apo'] = ta.APO(close, fastperiod=12, slowperiod=26, matype=0)
        df['ta_momentum_aroondown'], df['ta_momentum_aroonup'] = ta.AROON(high, low, timeperiod=14)
        df['ta_momentum_aroonosc'] = ta.AROONOSC(high, low, timeperiod=14)
        df['ta_momentum_bop'] = ta.BOP(open, high, low, close)
        df['ta_momentum_cci'] = ta.CCI(high, low, close, timeperiod=14)
        df['ta_momentum_cmo'] = ta.CMO(close, timeperiod=14)
        df['ta_momentum_dx'] = ta.DX(high, low, close, timeperiod=14)
        df['ta_momentum_macd_macd'], df['ta_momentum_macd_signal'], df['ta_momentum_macd_hist'] = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        df['ta_momentum_macdext_macd'], df['ta_momentum_macdext_signal'], df['ta_momentum_macdext_hist'] = ta.MACDEXT(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
        df['ta_momentum_macdfix_macd'], df['ta_momentum_macdfix_signal'], df['ta_momentum_macdfix_hist'] = ta.MACDFIX(close, signalperiod=9)
        df['ta_momentum_mfi'] = ta.MFI(high, low, close, volume, timeperiod=14)
        df['ta_momentum_minus_di'] = ta.MINUS_DI(high, low, close, timeperiod=14)
        df['ta_momentum_minus_dm'] = ta.MINUS_DM(high, low, timeperiod=14)
        df['ta_momentum_mom'] = ta.MOM(close, timeperiod=10)
        df['ta_momentum_plus_di'] = ta.PLUS_DI(high, low, close, timeperiod=14)
        df['ta_momentum_plus_dm'] = ta.PLUS_DM(high, low, timeperiod=14)
        df['ta_momentum_ppo'] = ta.PPO(close, fastperiod=12, slowperiod=26, matype=0)
        df['ta_momentum_roc'] = ta.ROC(close, timeperiod=10)
        df['ta_momentum_rocp'] = ta.ROCP(close, timeperiod=10)
        df['ta_momentum_rocr'] = ta.ROCR(close, timeperiod=10)
        df['ta_momentum_rocr100'] = ta.ROCR100(close, timeperiod=10)
        df['ta_momentum_rsi'] = ta.RSI(close, timeperiod=14)
        df['ta_momentum_slowk'], df['ta_momentum_slowd'] = ta.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        df['ta_momentum_fastk'], df['ta_momentum_fastd'] = ta.STOCHF(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0)
        df['ta_momentum_fastk'], df['ta_momentum_fastd'] = ta.STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
        df['ta_momentum_trix'] = ta.TRIX(close, timeperiod=12) # NOTE: Changed to avoid a lot of Nan values
        df['ta_momentum_ultosc'] = ta.ULTOSC(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28)
        df['ta_momentum_willr'] = ta.WILLR(high, low, close, timeperiod=14)

    if ta_settings['volume']:

        df['ta_volume_ad'] = ta.AD(high, low, close, volume)
        df['ta_volume_adosc'] = ta.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
        df['ta_volume_obv'] = ta.OBV(close, volume)

    if ta_settings['volatility']:

        df['ta_volatility_atr'] = ta.ATR(high, low, close, timeperiod=14)
        df['ta_volatility_natr'] = ta.NATR(high, low, close, timeperiod=14)
        df['ta_volatility_trange'] = ta.TRANGE(high, low, close)

    if ta_settings['price']:

        df['ta_price_avgprice'] = ta.AVGPRICE(open, high, low, close)
        df['ta_price_medprice'] = ta.MEDPRICE(high, low)
        df['ta_price_typprice'] = ta.TYPPRICE(high, low, close)
        df['ta_price_wclprice'] = ta.WCLPRICE(high, low, close)

    if ta_settings['cycle']:

        df['ta_cycle_ht_dcperiod'] = ta.HT_DCPERIOD(close)
        df['ta_cycle_ht_phasor_inphase'], df['ta_cycle_ht_phasor_quadrature'] = ta.HT_PHASOR(close)
        df['ta_cycle_ht_trendmode'] = ta.HT_TRENDMODE(close)

        # NOTE: Commented to avoid a lot of Nan values
        # df['ta_cycle_ht_dcphase'] = ta.HT_DCPHASE(close)
        # df['ta_cycle_ht_sine_sine'], df['ta_cycle_ht_sine_leadsine'] = ta.HT_SINE(close)

    if ta_settings['pattern']:

        df['ta_pattern_cdl2crows'] = ta.CDL2CROWS(open, high, low, close)
        df['ta_pattern_cdl3blackrows'] = ta.CDL3BLACKCROWS(open, high, low, close)
        df['ta_pattern_cdl3inside'] = ta.CDL3INSIDE(open, high, low, close)
        df['ta_pattern_cdl3linestrike'] = ta.CDL3LINESTRIKE(open, high, low, close)
        df['ta_pattern_cdl3outside'] = ta.CDL3OUTSIDE(open, high, low, close)
        df['ta_pattern_cdl3starsinsouth'] = ta.CDL3STARSINSOUTH(open, high, low, close)
        df['ta_pattern_cdl3whitesoldiers'] = ta.CDL3WHITESOLDIERS(open, high, low, close)
        df['ta_pattern_cdlabandonedbaby'] = ta.CDLABANDONEDBABY(open, high, low, close, penetration=0)
        df['ta_pattern_cdladvanceblock'] = ta.CDLADVANCEBLOCK(open, high, low, close)
        df['ta_pattern_cdlbelthold'] = ta.CDLBELTHOLD(open, high, low, close)
        df['ta_pattern_cdlbreakaway'] = ta.CDLBREAKAWAY(open, high, low, close)
        df['ta_pattern_cdlclosingmarubozu'] = ta.CDLCLOSINGMARUBOZU(open, high, low, close)
        df['ta_pattern_cdlconcealbabyswall'] = ta.CDLCONCEALBABYSWALL(open, high, low, close)
        df['ta_pattern_cdlcounterattack'] = ta.CDLCOUNTERATTACK(open, high, low, close)
        df['ta_pattern_cdldarkcloudcover'] = ta.CDLDARKCLOUDCOVER(open, high, low, close, penetration=0)
        df['ta_pattern_cdldoji'] = ta.CDLDOJI(open, high, low, close)
        df['ta_pattern_cdldojistar'] = ta.CDLDOJISTAR(open, high, low, close)
        df['ta_pattern_cdldragonflydoji'] = ta.CDLDRAGONFLYDOJI(open, high, low, close)
        df['ta_pattern_cdlengulfing'] = ta.CDLENGULFING(open, high, low, close)
        df['ta_pattern_cdleveningdojistar'] = ta.CDLEVENINGDOJISTAR(open, high, low, close, penetration=0)
        df['ta_pattern_cdleveningstar'] = ta.CDLEVENINGSTAR(open, high, low, close, penetration=0)
        df['ta_pattern_cdlgapsidesidewhite'] = ta.CDLGAPSIDESIDEWHITE(open, high, low, close)
        df['ta_pattern_cdlgravestonedoji'] = ta.CDLGRAVESTONEDOJI(open, high, low, close)
        df['ta_pattern_cdlhammer'] = ta.CDLHAMMER(open, high, low, close)
        df['ta_pattern_cdlhangingman'] = ta.CDLHANGINGMAN(open, high, low, close)
        df['ta_pattern_cdlharami'] = ta.CDLHARAMI(open, high, low, close)
        df['ta_pattern_cdlharamicross'] = ta.CDLHARAMICROSS(open, high, low, close)
        df['ta_pattern_cdlhighwave'] = ta.CDLHIGHWAVE(open, high, low, close)
        df['ta_pattern_cdlhikkake'] = ta.CDLHIKKAKE(open, high, low, close)
        df['ta_pattern_cdlhikkakemod'] = ta.CDLHIKKAKEMOD(open, high, low, close)
        df['ta_pattern_cdlhomingpigeon'] = ta.CDLHOMINGPIGEON(open, high, low, close)
        df['ta_pattern_cdlidentical3crows'] = ta.CDLIDENTICAL3CROWS(open, high, low, close)
        df['ta_pattern_cdlinneck'] = ta.CDLINNECK(open, high, low, close)
        df['ta_pattern_cdlinvertedhammer'] = ta.CDLINVERTEDHAMMER(open, high, low, close)
        df['ta_pattern_cdlkicking'] = ta.CDLKICKING(open, high, low, close)
        df['ta_pattern_cdlkickingbylength'] = ta.CDLKICKINGBYLENGTH(open, high, low, close)
        df['ta_pattern_cdlladderbottom'] = ta.CDLLADDERBOTTOM(open, high, low, close)
        df['ta_pattern_cdllongleggeddoji'] = ta.CDLLONGLEGGEDDOJI(open, high, low, close)
        df['ta_pattern_cdllongline'] = ta.CDLLONGLINE(open, high, low, close)
        df['ta_pattern_cdlmarubozu'] = ta.CDLMARUBOZU(open, high, low, close)
        df['ta_pattern_cdlmatchinglow'] = ta.CDLMATCHINGLOW(open, high, low, close)
        df['ta_pattern_cdlmathold'] = ta.CDLMATHOLD(open, high, low, close, penetration=0)
        df['ta_pattern_cdlmorningdojistar'] = ta.CDLMORNINGDOJISTAR(open, high, low, close, penetration=0)
        df['ta_pattern_cdlmorningstar'] = ta.CDLMORNINGSTAR(open, high, low, close, penetration=0)
        df['ta_pattern_cdllonneck'] = ta.CDLONNECK(open, high, low, close)
        df['ta_pattern_cdlpiercing'] = ta.CDLPIERCING(open, high, low, close)
        df['ta_pattern_cdlrickshawman'] = ta.CDLRICKSHAWMAN(open, high, low, close)
        df['ta_pattern_cdlrisefall3methods'] = ta.CDLRISEFALL3METHODS(open, high, low, close)
        df['ta_pattern_cdlseparatinglines'] = ta.CDLSEPARATINGLINES(open, high, low, close)
        df['ta_pattern_cdlshootingstar'] = ta.CDLSHOOTINGSTAR(open, high, low, close)
        df['ta_pattern_cdlshortline'] = ta.CDLSHORTLINE(open, high, low, close)
        df['ta_pattern_cdlspinningtop'] = ta.CDLSPINNINGTOP(open, high, low, close)
        df['ta_pattern_cdlstalledpattern'] = ta.CDLSTALLEDPATTERN(open, high, low, close)
        df['ta_pattern_cdlsticksandwich'] = ta.CDLSTICKSANDWICH(open, high, low, close)
        df['ta_pattern_cdltakuri'] = ta.CDLTAKURI(open, high, low, close)
        df['ta_pattern_cdltasukigap'] = ta.CDLTASUKIGAP(open, high, low, close)
        df['ta_pattern_cdlthrusting'] = ta.CDLTHRUSTING(open, high, low, close)
        df['ta_pattern_cdltristar'] = ta.CDLTRISTAR(open, high, low, close)
        df['ta_pattern_cdlunique3river'] = ta.CDLUNIQUE3RIVER(open, high, low, close)
        df['ta_pattern_cdlupsidegap2crows'] = ta.CDLUPSIDEGAP2CROWS(open, high, low, close)
        df['ta_pattern_cdlxsidegap3methods'] = ta.CDLXSIDEGAP3METHODS(open, high, low, close)

    if ta_settings['statistic']:

        df['ta_statistic_beta'] = ta.BETA(high, low, timeperiod=5)
        df['ta_statistic_correl'] = ta.CORREL(high, low, timeperiod=30)
        df['ta_statistic_linearreg'] = ta.LINEARREG(close, timeperiod=14)
        df['ta_statistic_linearreg_angle'] = ta.LINEARREG_ANGLE(close, timeperiod=14)
        df['ta_statistic_linearreg_intercept'] = ta.LINEARREG_INTERCEPT(close, timeperiod=14)
        df['ta_statistic_linearreg_slope'] = ta.LINEARREG_SLOPE(close, timeperiod=14)
        df['ta_statistic_stddev'] = ta.STDDEV(close, timeperiod=5, nbdev=1)
        df['ta_statistic_tsf'] = ta.TSF(close, timeperiod=14)
        df['ta_statistic_var'] = ta.VAR(close, timeperiod=5, nbdev=1)

    if ta_settings['math_transforms']:

        df['ta_math_transforms_atan'] = ta.ATAN(close)
        df['ta_math_transforms_ceil'] = ta.CEIL(close)
        df['ta_math_transforms_cos'] = ta.COS(close)
        df['ta_math_transforms_floor'] = ta.FLOOR(close)
        df['ta_math_transforms_ln'] = ta.LN(close)
        df['ta_math_transforms_log10'] = ta.LOG10(close)
        df['ta_math_transforms_sin'] = ta.SIN(close)
        df['ta_math_transforms_sqrt'] = ta.SQRT(close)
        df['ta_math_transforms_tan'] = ta.TAN(close)

    if ta_settings['math_operators']:

        df['ta_math_operators_add'] = ta.ADD(high, low)
        df['ta_math_operators_div'] = ta.DIV(high, low)
        df['ta_math_operators_min'], df['ta_math_operators_max'] = ta.MINMAX(close, timeperiod=30)
        df['ta_math_operators_minidx'], df['ta_math_operators_maxidx'] = ta.MINMAXINDEX(close, timeperiod=30)
        df['ta_math_operators_mult'] = ta.MULT(high, low)
        df['ta_math_operators_sub'] = ta.SUB(high, low)
        df['ta_math_operators_sum'] = ta.SUM(close, timeperiod=30)

    return df


def add_fbprophet_features(df, data_freq, minute_freq, fbprophet_settings):
    """
    """
    df_prophet = df[['timestamp', 'price']]
    df_prophet.columns = ['ds', 'y']

    m = Prophet().fit(df_prophet)

    if data_freq == "daily":
        freq = 'D'
    else:
        freq = 'min'

    future = m.make_future_dataframe(periods=int(minute_freq), freq=freq) # TODO: parametrizar el número de minutos...
    forecast = m.predict(future)

    # build a new feature
    df_prophet = df_prophet.shift(-1)
    listado = df_prophet.y.tolist()
    listado[-1] = forecast.iloc[-1]['yhat']
    df['fbprophet'] = listado

    return df


def add_tsfresh_features(df, tsfresh_settings):
    """Automatic extraction of relevant features from time series.
    http://tsfresh.readthedocs.io
    https://github.com/blue-yonder/tsfresh
    """
    pass
    """
    # Prepare some columns useful for tsfresh
    n = df.shape[0]
    df['id'] = 1
    df['time'] = np.array(range(1, n + 1))
    excl = ['target', 'pred', 'timestamp']
    cols = [c for c in df.columns if c not in excl]

    # Prepare rolling
    df_id_changed = roll_time_series(df[cols], column_id="id",
                            column_sort="time", column_kind=None,
                            rolling_direction=1,
                            max_timeshift=tsfresh_settings['window'])

    # Extract tsfresh features
    extracted_features = extract_features(df_id_changed,
                            default_fc_parameters=tsfresh_settings['method'],
                            column_id="id", column_sort="time",
                            disable_progressbar=True, n_jobs=os.cpu_count())

    # merge originals and new features
    extracted_features['time'] = np.array(range(1, n + 1))
    df_tsfresh = pd.merge(df, extracted_features, on=['time'])

    excl = ['id', 'time']
    cols = [c for c in df_tsfresh.columns if c not in excl]

    return df_tsfresh[cols]
    """
