"""Promote the step 09 candidate to the model in use.

Builds models/chl_forecast_step09.joblib from the candidate saved by
09-Model-Improvements.ipynb, adding what the live forecast needs (grid
coordinates, the distance-to-coast map, labelled climatologies), and checks that
the result reproduces the candidate's 2025 test scores through the shared code
before saving. The step 05 model is not changed.

Run from experiment_v2/:

    .venv/bin/python scripts/promote_step09_model.py
"""

from pathlib import Path
from datetime import datetime, timezone
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chlforecast import config, forecast  # noqa: E402
from chlforecast import features as F  # noqa: E402

candidate = joblib.load(config.STEP09_CANDIDATE_PATH)
print(f"Candidate from {candidate['created_utc'][:16]} UTC, {len(candidate['feature_names'])} inputs, "
      f"residual on blend: {candidate['residual_on_blend']}")
if candidate["residual_on_blend"]:
    sys.exit("This script promotes direct models only (the step 09 winner); the candidate predicts a residual.")
if list(candidate["feature_names"]) != config.MODEL_FEATURES:
    sys.exit(f"Candidate inputs {candidate['feature_names']} differ from config.MODEL_FEATURES.")

with xr.open_dataset(config.PROCESSED / "malta_daily_observations.nc") as observations:
    latitude = observations.latitude.values
    longitude = observations.longitude.values
with xr.open_dataset(config.DATA / "chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc") as l4:
    sea = np.isfinite(l4["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)

coords = {"latitude": latitude, "longitude": longitude}
grid = ("latitude", "longitude")
monthly = {"month": np.arange(1, 13), **coords}
horizons = list(config.FORECAST_HORIZONS)

bundle = {
    "models": {int(h): m for h, m in candidate["models"].items()},
    "feature_names": list(candidate["feature_names"]),
    "feature_set": "Step 05 inputs + 7 new inputs (step 09)",
    "forecast_horizons_days": horizons,
    "forecast_issue_time_utc": config.FORECAST_ISSUE_TIME_UTC,
    "target_transform": "log10",
    "target_units": "milligram m^-3",
    "preprocessing": {
        "chl_availability_lag_days": config.CHL_LAG_DAYS,
        "sst_availability_lag_days": config.SST_LAG_DAYS,
        "chl_history_window_days": config.CHL_HISTORY_DAYS,
        "sst_units": "degree_Celsius",
        "max_plausible_chl_mg_m3": config.MAX_PLAUSIBLE_CHL,
        "min_plausible_chl_mg_m3": candidate["min_plausible_chl"],
        "min_training_observations_per_pixel": config.MIN_TRAINING_OBSERVATIONS,
    },
    "training_issue_date_range": ["2017-01-01", "2024-12-24"],
    "train_sample_fraction": 0.6,
    "model_settings": candidate["model_settings"],
    "model_mask": xr.DataArray(np.asarray(candidate["model_mask"]).astype("uint8"), dims=grid, coords=coords),
    "monthly_log_climatology": xr.DataArray(candidate["monthly_log_climatology"], dims=("month", *grid), coords=monthly),
    "monthly_sst_climatology": xr.DataArray(candidate["monthly_sst_climatology"], dims=("month", *grid), coords=monthly),
    "coast_distance_km": xr.DataArray(F.coast_distance_km(sea, latitude, longitude), dims=grid, coords=coords),
    "climatology_period": "2017–2023",
    "damped_persistence_coefficients": {int(h): list(c) for h, c in candidate["damped_persistence_coefficients"].items()},
    "residual_on_blend": False,
    "test_year": 2025,
    "screening": candidate["screening"],
    "test_gains": candidate["test_gains"],
    "test_scores": candidate["test_scores"],
    "promoted_from": config.STEP09_CANDIDATE_PATH.name,
    "candidate_created_utc": candidate["created_utc"],
    "sklearn_version": sklearn.__version__,
    "created_utc": datetime.now(timezone.utc).isoformat(),
}

print("Checking the promoted model against the candidate's 2025 test scores (a few minutes)...")
rerun = forecast.test_year_scores(bundle)
failed = False
for h in horizons:
    saved = next(r for r in candidate["test_scores"] if r["Horizon"] == f"+{h}d" and r["Method"] == "New model")
    rmse, n = rerun[h]
    ok = abs(rmse - saved["RMSE (log10)"]) < 1e-6 and n == saved["Scored pixel-days"]
    failed |= not ok
    print(f"  {'ok  ' if ok else 'FAIL'} +{h}d  {n:,} pixel-days  log RMSE candidate {saved['RMSE (log10)']:.6f}  promoted {rmse:.6f}")
if failed:
    sys.exit("Not saved: the promoted model does not reproduce the candidate's scores.")

joblib.dump(bundle, config.MODEL_PATH, compress=3)
print(f"Saved the model in use: {config.MODEL_PATH} ({config.MODEL_PATH.stat().st_size / 1024**2:.1f} MB)")
