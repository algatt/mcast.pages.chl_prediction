"""The input recipe, shared by training (step 04) and the live forecast (step 07).

All functions work on plain numpy arrays shaped (time, latitude, longitude),
on a complete daily calendar (one slice per day, missing values as NaN).
"Observation day" arrays are indexed by the day the satellite measured;
"issue day" arrays by the day the forecast is made.
"""

import warnings

import numpy as np
import pandas as pd
import xarray as xr

from . import config


def quality_control(chl, minimum=None):
    """Treat implausible chlorophyll as missing (step 04): values above
    MAX_PLAUSIBLE_CHL become NaN, and values below `minimum` if one is given
    (step 09 tests config.MIN_PLAUSIBLE_CHL). Returns a new array."""
    chl = np.asarray(chl, dtype="float32")
    with np.errstate(invalid="ignore"):
        keep = chl <= config.MAX_PLAUSIBLE_CHL
        if minimum is not None:
            keep &= chl >= minimum
        return np.where(keep, chl, np.nan).astype("float32")


def shift_to_issue_days(values, lag_days):
    """Move observation-day values to the first issue day they are usable:
    the value measured on day t becomes available on day t + lag_days."""
    values = np.asarray(values)
    if lag_days == 0:
        return values.copy()
    out = np.full(values.shape, np.nan, dtype=values.dtype)
    out[lag_days:] = values[:-lag_days]
    return out


def season_features(dates):
    """Day of the year as two smooth numbers, so 31 December sits next to 1 January."""
    dates = pd.DatetimeIndex(dates)
    year_lengths = np.where(dates.is_leap_year, 366, 365)
    phase = 2 * np.pi * (dates.dayofyear.to_numpy() - 1) / year_lengths
    return np.sin(phase).astype("float32"), np.cos(phase).astype("float32")


def model_mask(chl, dates, period=None):
    """Pixels observed at least MIN_TRAINING_OBSERVATIONS times in the training period."""
    dates = pd.DatetimeIndex(dates)
    start, end = period or config.SPLIT_PERIODS["train"]
    in_period = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    counts = np.isfinite(chl[in_period]).sum(axis=0)
    return counts >= config.MIN_TRAINING_OBSERVATIONS, counts


def chl_history_features(chl, mask=None, lag_days=None, window=None):
    """Chlorophyll inputs for every issue day, from observation-day chlorophyll.

    Returns a dict of issue-day arrays:
      chl_latest          most recent usable observation, however old
      chl_age_days        days between that observation and the issue day
      chl_mean_7d         mean of the usable observations in the past `window` days
      chl_observations_7d how many observations that mean is based on (0 to window)

    Only observations from before the issue day (by `lag_days`) are used.
    Pixels outside `mask` are NaN (counts 0).
    """
    lag_days = config.CHL_LAG_DAYS if lag_days is None else lag_days
    window = config.CHL_HISTORY_DAYS if window is None else window
    available = shift_to_issue_days(np.asarray(chl, dtype="float32"), lag_days)
    if mask is not None:
        available = np.where(mask[None], available, np.nan).astype("float32")

    finite = np.isfinite(available)
    day = np.arange(available.shape[0], dtype=np.int32)[:, None, None]
    last = np.maximum.accumulate(np.where(finite, day, -1), axis=0)
    latest = np.take_along_axis(available, np.maximum(last, 0), axis=0)
    age = (day - last + lag_days).astype("float32")
    latest[last < 0] = np.nan
    age[last < 0] = np.nan

    # Rolling mean and count over the past `window` issue-day slots. xarray's
    # rolling mean is used so the values match the ones the model was trained
    # on to the last bit (it accumulates in float32).
    rolling = xr.DataArray(available, dims=("time", "y", "x")).rolling(time=window, min_periods=1)
    mean = rolling.mean().values.astype("float32")
    count = rolling.count().fillna(0).values

    if mask is not None:
        latest = np.where(mask[None], latest, np.nan)
        age = np.where(mask[None], age, np.nan)
        mean = np.where(mask[None], mean, np.nan)
    return {
        "chl_latest": latest.astype("float32"),
        "chl_age_days": age.astype("float32"),
        "chl_mean_7d": mean.astype("float32"),
        "chl_observations_7d": count.astype("uint8"),
    }


def monthly_log_climatology(chl, dates, mask, period=None):
    """Median log10 chlorophyll for each calendar month at each pixel, from the
    training period only. Months without observations use the pixel's overall
    median. Returns an array shaped (12, latitude, longitude); index 0 is January."""
    dates = pd.DatetimeIndex(dates)
    start, end = period or config.SPLIT_PERIODS["train"]
    in_period = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    with np.errstate(divide="ignore", invalid="ignore"):
        log_chl = np.log10(np.where(mask[None], chl[in_period], np.nan))
    months = dates[in_period].month.to_numpy()
    clim = np.empty((12,) + log_chl.shape[1:], dtype="float32")
    with warnings.catch_warnings():
        # Pixels never observed (land) give all-NaN medians; that is expected.
        warnings.simplefilter("ignore", RuntimeWarning)
        overall = np.nanmedian(log_chl, axis=0)
        for m in range(1, 13):
            clim[m - 1] = np.nanmedian(log_chl[months == m], axis=0)
    clim = np.where(np.isfinite(clim), clim, overall[None]).astype("float32")
    return np.where(mask[None], clim, np.nan).astype("float32")


def climatology_for_dates(monthly_log_clim, dates):
    """The monthly log10 climatology looked up for each date: (time, latitude, longitude)."""
    months = pd.DatetimeIndex(dates).month.to_numpy()
    return monthly_log_clim[months - 1]


def sst_features(sst, mask=None, lag_days=None):
    """Sea temperature on each issue day, and whether it was observed."""
    lag_days = config.SST_LAG_DAYS if lag_days is None else lag_days
    sst = shift_to_issue_days(np.asarray(sst, dtype="float32"), lag_days)
    if mask is not None:
        sst = np.where(mask[None], sst, np.nan).astype("float32")
    return {"sst_c": sst, "sst_observed": np.isfinite(sst).astype("uint8")}


def forecast_inputs(chl, sst, dates, mask, monthly_log_clim, latitude, longitude):
    """The model's 11 inputs (config.FINAL_FEATURES) for every issue day in `dates`.

    `chl` and `sst` are observation-day arrays on the same daily calendar as
    `dates`. Used by step 04 for the archive and by step 07 for live data.
    """
    dates = pd.DatetimeIndex(dates)
    shape = (len(dates), len(latitude), len(longitude))
    sin, cos = season_features(dates)
    inputs = {
        "season_sin": np.broadcast_to(sin[:, None, None], shape),
        "season_cos": np.broadcast_to(cos[:, None, None], shape),
        **chl_history_features(chl, mask),
        "latitude_deg": np.broadcast_to(np.asarray(latitude, "float32")[None, :, None], shape),
        "longitude_deg": np.broadcast_to(np.asarray(longitude, "float32")[None, None, :], shape),
        "chl_clim_log": climatology_for_dates(monthly_log_clim, dates),
        **sst_features(sst, mask),
    }
    return {name: inputs[name] for name in config.FINAL_FEATURES}


# --- Extra inputs tested in step 09 ----------------------------------------------


def neighbourhood_mean(values, size):
    """Mean of the valid values within a size × size block of pixels around each
    pixel, day by day (NaN where the block has none)."""
    from scipy.ndimage import uniform_filter

    values = np.asarray(values, dtype="float32")
    finite = np.isfinite(values)
    window = (1, size, size) if values.ndim == 3 else (size, size)
    total = uniform_filter(np.where(finite, values, 0).astype("float32"), size=window, mode="constant")
    share = uniform_filter(finite.astype("float32"), size=window, mode="constant")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(share > 0.5 / size ** 2, total / share, np.nan).astype("float32")


def coast_distance_km(sea, latitude, longitude):
    """Distance from each pixel to the nearest land pixel, in km."""
    from scipy.ndimage import distance_transform_edt

    latitude = np.asarray(latitude)
    dy = 111.2 * float(np.median(np.abs(np.diff(latitude))))
    dx = 111.2 * float(np.median(np.abs(np.diff(longitude)))) * np.cos(np.deg2rad(latitude.mean()))
    return distance_transform_edt(np.asarray(sea, dtype=bool), sampling=(dy, dx)).astype("float32")


def monthly_climatology(values, dates, mask, period=None):
    """Median of `values` for each calendar month at each pixel, training period only
    (like monthly_log_climatology, but on the values as given)."""
    dates = pd.DatetimeIndex(dates)
    start, end = period or config.SPLIT_PERIODS["train"]
    in_period = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    selected = np.where(mask[None], values[in_period], np.nan)
    months = dates[in_period].month.to_numpy()
    clim = np.empty((12,) + selected.shape[1:], dtype="float32")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        overall = np.nanmedian(selected, axis=0)
        for m in range(1, 13):
            clim[m - 1] = np.nanmedian(selected[months == m], axis=0)
    return np.where(np.isfinite(clim), clim, overall[None]).astype("float32")


def extra_inputs(chl, sst, dates, base, sea, latitude, longitude, mask, monthly_sst_clim, coast_km=None):
    """The candidate inputs of step 09, from observation-day `chl` and `sst` and
    the step 04 inputs in `base` (from forecast_inputs). All use only data
    available at issue time. Distance to the coast comes from `coast_km` if
    given, otherwise it is computed from the `sea` mask."""
    available = shift_to_issue_days(np.asarray(chl, dtype="float32"), config.CHL_LAG_DAYS)
    sst_issue = shift_to_issue_days(np.asarray(sst, dtype="float32"), config.SST_LAG_DAYS)
    with np.errstate(divide="ignore", invalid="ignore"):
        latest_log = np.log10(base["chl_latest"])
        mean_log = np.log10(base["chl_mean_7d"])

    # Temperature change: today's value minus the mean of the previous 7 days.
    previous = xr.DataArray(shift_to_issue_days(sst_issue, 1), dims=("time", "y", "x"))
    sst_week = previous.rolling(time=config.CHL_HISTORY_DAYS, min_periods=1).mean().values

    shape = available.shape
    out = {
        "chl_nbr5_yesterday": neighbourhood_mean(available, 5),
        "chl_nbr15_7d": neighbourhood_mean(base["chl_mean_7d"], 15),
        "chl_trend_log": (latest_log - mean_log).astype("float32"),
        "chl_anomaly_log": (latest_log - base["chl_clim_log"]).astype("float32"),
        "sst_anomaly": (sst_issue - climatology_for_dates(monthly_sst_clim, dates)).astype("float32"),
        "sst_change_7d": (sst_issue - sst_week).astype("float32"),
        "coast_distance_km": np.broadcast_to(
            (coast_km if coast_km is not None else coast_distance_km(sea, latitude, longitude))[None], shape),
    }
    return {k: (np.where(mask[None], v, np.nan).astype("float32") if k != "coast_distance_km" else v)
            for k, v in out.items()}


def model_inputs(chl, sst, dates, mask, monthly_log_clim, monthly_sst_clim, coast_km, latitude, longitude):
    """All inputs of the model in use (config.MODEL_FEATURES), for every issue day.

    Used by the live forecast (step 07) and by the checks. `chl` should already
    have the quality rule applied (quality_control with MIN_PLAUSIBLE_CHL)."""
    base = forecast_inputs(chl, sst, dates, mask, monthly_log_clim, latitude, longitude)
    extra = extra_inputs(chl, sst, dates, base, None, latitude, longitude, mask, monthly_sst_clim,
                         coast_km=np.asarray(coast_km, dtype="float32"))
    inputs = {**base, **extra}
    return {name: inputs[name] for name in config.MODEL_FEATURES}
