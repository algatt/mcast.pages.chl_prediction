"""Issuing forecasts with the saved model (steps 06 and 07)."""

import numpy as np
import pandas as pd

from . import features as F


def model_forecast(bundle, inputs, issue_dates, horizon):
    """Forecast chlorophyll (mg/m³) `horizon` days ahead, for every issue day and
    every modelled pixel, from inputs built by features.forecast_inputs.

    Pixels with no chlorophyll history get the usual value for the target month:
    the model was hardly ever trained on such pixels (see step 07).
    Returns an array (time, latitude, longitude), NaN outside the model mask.
    """
    mask = bundle["model_mask"].values == 1
    names = bundle["feature_names"]
    shape = inputs["chl_latest"].shape
    t, i, j = np.nonzero(np.broadcast_to(mask, shape))
    X = pd.DataFrame({name: np.asarray(inputs[name])[t, i, j] for name in names}).astype("float32")

    prediction = 10.0 ** bundle["models"][horizon].predict(X[names])
    clim = bundle["monthly_log_climatology"].values
    target_dates = pd.DatetimeIndex(issue_dates) + pd.Timedelta(days=int(horizon))
    fallback = 10.0 ** F.climatology_for_dates(clim, target_dates)[t, i, j]
    prediction = np.where(np.isfinite(X["chl_latest"].to_numpy()), prediction, fallback)

    out = np.full(shape, np.nan, dtype="float32")
    out[t, i, j] = prediction
    return out


def blend_forecast(bundle, inputs, issue_dates, horizon):
    """The blend rule (damped persistence) for the same issue days and pixels."""
    clim = bundle["monthly_log_climatology"].values
    target_dates = pd.DatetimeIndex(issue_dates) + pd.Timedelta(days=int(horizon))
    target_clim = F.climatology_for_dates(clim, target_dates)
    a, b, c = bundle["damped_persistence_coefficients"][horizon]
    with np.errstate(divide="ignore", invalid="ignore"):
        latest_log = np.log10(inputs["chl_latest"])
    blended = np.where(np.isfinite(latest_log), a + b * latest_log + c * target_clim, target_clim)
    mask = bundle["model_mask"].values == 1
    return np.where(mask[None], 10.0 ** blended, np.nan).astype("float32")


def test_year_scores(bundle, history_start="2016-12-01"):
    """Re-score a bundle of the model in use on the test year, from the collated
    observations, with inputs built by the shared recipe (features.model_inputs).
    Returns {horizon: (log10 RMSE, scored pixel-days)}. Used to verify that the
    model and the recipe agree; forecasts are stored as float32, so scores agree
    to about 1e-8, not exactly."""
    import xarray as xr
    from . import config

    with xr.open_dataset(config.PROCESSED / "malta_daily_observations.nc") as observations:
        observations = observations.sel(time=slice(history_start, None)).load()
    dates = pd.DatetimeIndex(observations.time.values)
    grid = ("time", "latitude", "longitude")
    chl = F.quality_control(observations["chl"].transpose(*grid).values,
                            minimum=bundle["preprocessing"]["min_plausible_chl_mg_m3"])
    sst = observations["sst_c"].transpose(*grid).values
    mask = bundle["model_mask"].values == 1
    inputs = F.model_inputs(chl, sst, dates, mask, bundle["monthly_log_climatology"].values,
                            bundle["monthly_sst_climatology"].values, bundle["coast_distance_km"].values,
                            observations.latitude.values, observations.longitude.values)

    horizons = [int(h) for h in bundle["forecast_horizons_days"]]
    start, end = config.SPLIT_PERIODS["test"]
    in_test = (dates >= pd.Timestamp(start)) & (dates + pd.Timedelta(days=max(horizons)) <= pd.Timestamp(end))
    days = np.flatnonzero(in_test)
    block = slice(days[0], days[-1] + 1)
    block_inputs = {name: np.broadcast_to(values, chl.shape)[block] for name, values in inputs.items()}

    scores = {}
    for h in horizons:
        predicted = model_forecast(bundle, block_inputs, dates[block], h)
        target = np.full(chl.shape, np.nan, dtype="float32")
        target[:-h] = chl[h:]
        target = target[block]
        valid = np.isfinite(target) & (target > 0) & mask[None] & in_test[block][:, None, None]
        error = np.log10(predicted[valid]) - np.log10(target[valid])
        scores[h] = (float(np.sqrt(np.mean(error ** 2))), int(valid.sum()))
    return scores
