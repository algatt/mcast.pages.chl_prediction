"""Check that the shared code in chlforecast/ reproduces the experiment's files.

1. Rebuilds the model inputs from the collated observations with
   chlforecast.features and compares them with the prepared file from step 04.
2. Re-scores the saved model and the simple rules on the 2025 test year with
   chlforecast.samples, .baselines and .scoring, and compares the scores with
   those saved in the model file by step 05.

Run from experiment_v2/ after any change to chlforecast/:

    .venv/bin/python scripts/check_shared_code.py
"""

from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chlforecast import baselines, config, features, samples, scoring  # noqa: E402

failures = []


def compare(name, rebuilt, saved, tolerance=0.0):
    rebuilt = np.asarray(rebuilt, dtype="float64")
    saved = np.asarray(saved, dtype="float64")
    same_gaps = np.array_equal(np.isnan(rebuilt), np.isnan(saved))
    both = np.isfinite(rebuilt) & np.isfinite(saved)
    worst = float(np.max(np.abs(rebuilt[both] - saved[both]) / np.maximum(1, np.abs(saved[both])))) if both.any() else 0.0
    ok = same_gaps and worst <= tolerance
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<22} gaps identical: {same_gaps}, largest difference: {worst:.2e}")
    if not ok:
        failures.append(name)


print("1. Model inputs against the prepared file (step 04)")
observations = xr.open_dataset(config.PROCESSED / "malta_daily_observations.nc")
prepared = xr.open_dataset(config.PROCESSED / "malta_forecast_prepared.nc")
dates = pd.DatetimeIndex(observations.time.values)

chl = features.quality_control(observations["chl"].transpose("time", "latitude", "longitude").values)
sst = observations["sst_c"].transpose("time", "latitude", "longitude").values
mask, _ = features.model_mask(chl, dates)
compare("model_mask", mask, prepared["model_mask"].values == 1, tolerance=0)

clim = features.monthly_log_climatology(chl, dates, mask)
inputs = features.forecast_inputs(chl, sst, dates, mask, clim,
                                  observations.latitude.values, observations.longitude.values)
for name in config.FINAL_FEATURES:
    saved = prepared[name]
    if saved.dims == ("time",):
        rebuilt = inputs[name][:, 0, 0]
    elif saved.dims == ("latitude",):
        rebuilt = inputs[name][0, :, 0]
    elif saved.dims == ("longitude",):
        rebuilt = inputs[name][0, 0, :]
    else:
        rebuilt = inputs[name]
        saved = saved.transpose("time", "latitude", "longitude")
    compare(name, rebuilt, saved.values)

for h in config.FORECAST_HORIZONS:
    rebuilt_target = np.full(chl.shape, np.nan, dtype="float32")
    rebuilt_target[:-h] = chl[h:]
    compare(f"chl_target_{h}d", rebuilt_target,
            prepared[f"chl_target_{h}d"].transpose("time", "latitude", "longitude").values)

print("\n2. Test-year scores against the saved model (step 05)")
bundle = joblib.load(config.MODEL_PATH)
saved_scores = bundle["test_results"]
for h in config.FORECAST_HORIZONS:
    test = samples.make_samples(prepared, "test", h, bundle["feature_names"])
    predictions = baselines.baseline_predictions(test["persistence"], test["clim_log"],
                                                 bundle["damped_persistence_coefficients"][h])
    predictions["Forecast model"] = 10.0 ** bundle["models"][h].predict(test["X"][bundle["feature_names"]])
    for method, predicted in predictions.items():
        rerun = scoring.chl_scores(test["observed"], predicted)["RMSE (log10)"]
        saved = saved_scores.loc[(f"+{h}d", method), "RMSE (log10)"]
        ok = abs(rerun - saved) < 1e-9
        print(f"  {'ok  ' if ok else 'FAIL'} +{h}d {method:<26} saved {saved:.6f}  re-run {rerun:.6f}")
        if not ok:
            failures.append(f"+{h}d {method}")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    sys.exit(1)
print("All checks passed: the shared code reproduces steps 04 and 05.")
