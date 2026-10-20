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
