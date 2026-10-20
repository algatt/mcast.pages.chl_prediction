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


def quality_control(chl):
    """Treat implausible chlorophyll as missing (step 04): values above
    MAX_PLAUSIBLE_CHL become NaN. Returns a new array."""
    chl = np.asarray(chl, dtype="float32")
    with np.errstate(invalid="ignore"):
        return np.where(chl <= config.MAX_PLAUSIBLE_CHL, chl, np.nan).astype("float32")


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
