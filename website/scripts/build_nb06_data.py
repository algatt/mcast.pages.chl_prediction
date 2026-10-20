"""Build the data behind the Step 06 page (06-Forecast-Maps.ipynb).

Re-runs the saved model on the 2025 test year (checked against the saved test
scores first) and saves website/src/data/nb06.json:
  * forecast and observed maps for the notebook's two example issue days;
  * per-pixel maps over 2025: winter bias, typical error, and gain over the
    blend rule (damped persistence), for +1 and +7 days.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb06_data.py
"""

from pathlib import Path
import base64
import json

import joblib
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
BUNDLE = EXP / "models/chl_forecast_1_4_7d.joblib"
PREPARED = EXP / "data/processed/malta_forecast_prepared.nc"
L4 = EXP / "data/chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
OUT_PATH = ROOT / "website/src/data/nb06.json"

EXAMPLE_DAYS = ["2025-02-15", "2025-08-15"]      # as in the notebook
MAP_HORIZONS = [1, 7]
MIN_PAIRS = 30                                   # per pixel, for per-pixel statistics
WINTER = {12, 1, 2}

bundle = joblib.load(BUNDLE)
features = bundle["feature_names"]
data = xr.open_dataset(PREPARED)
mask = data["model_mask"].values == 1
with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)

in_test = data["split_test"].values == 1
days = np.flatnonzero(in_test)
block = slice(days[0], days[-1] + 1)
subset = data.isel(time=block).load()
issue_dates = pd.DatetimeIndex(subset.time.values)
T, NY, NX = subset.sizes["time"], subset.sizes["latitude"], subset.sizes["longitude"]


def grid(name, ds=subset):
    return ds[name].transpose("time", "latitude", "longitude").values


def predict_all(h):
    """Model, blend and persistence forecasts for every issue day and modelled pixel."""
    t, i, j = np.nonzero(np.broadcast_to(mask, (T, NY, NX)))
    columns = {}
    for name in features:
        dims = subset[name].dims
        if dims == ("time",):
            columns[name] = subset[name].values[t]
        elif dims == ("latitude",):
            columns[name] = subset[name].values[i]
        elif dims == ("longitude",):
            columns[name] = subset[name].values[j]
        else:
            columns[name] = grid(name)[t, i, j]
    X = pd.DataFrame(columns).astype("float32")
    model = np.full((T, NY, NX), np.nan)
    model[t, i, j] = 10 ** bundle["models"][h].predict(X[features])
    persistence = grid("chl_latest")
    clim_log = grid("chl_clim_log", data["chl_clim_log"].shift(time=-h).isel(time=block).to_dataset())
    a, b, c = bundle["damped_persistence_coefficients"][h]
    damped = 10 ** (a + b * np.log10(persistence) + c * clim_log)
    return model, damped, persistence


# Maps are packed one byte per pixel (0–254 across a fixed range, 255 = no
# value) and base64-encoded; src/data/packed.js unpacks them. The ranges keep
# display precision within a few per cent.
RANGES = {
    "log_chl": (-2.0, 1.0),          # log10 mg/m³
    "bias": (-0.1, 0.1),             # mg/m³
    "log_rmse": (0.0, 0.5),          # log10
    "gain": (-50.0, 50.0),           # %
}


def pack(field, kind):
    lo, hi = RANGES[kind]
    ok = np.isfinite(field) & sea
    q = np.full(field.shape, 255, dtype=np.uint8)
    q[ok] = np.rint((np.clip(field[ok], lo, hi) - lo) / (hi - lo) * 254).astype(np.uint8)
    return {"kind": kind, "range": [lo, hi], "data": base64.b64encode(q.tobytes()).decode("ascii")}


def log_or_nan(field):
    with np.errstate(all="ignore"):
        return np.where(field > 0, np.log10(field), np.nan)


examples = {d: {} for d in EXAMPLE_DAYS}
pixel_maps = {}
pixel_stats = {}
checks = []
for h in [1, 4, 7]:
    model, damped, persistence = predict_all(h)
    target = grid(f"chl_target_{h}d")
    scored = np.isfinite(target) & (target > 0) & mask[None] & in_test[block][:, None, None]

    # Check against the saved test score.
    err = np.log10(model[scored]) - np.log10(target[scored])
    rerun = float(np.sqrt(np.mean(err ** 2)))
    saved = bundle["test_results"].loc[(f"+{h}d", "Forecast model"), "RMSE (log10)"]
    checks.append((h, saved, rerun))
    assert abs(saved - rerun) < 1e-9, (h, saved, rerun)

    # Example days
    for d in EXAMPLE_DAYS:
        k = issue_dates.get_loc(pd.Timestamp(d))
        obs = np.where(scored[k], target[k], np.nan)
        sel = scored[k]
        log_err = {m: np.log10(f[k][sel]) - np.log10(target[k][sel])
                   for m, f in [("model", model), ("damped", damped), ("persistence", persistence)]}
        examples[d][h] = {
            "target_date": str((pd.Timestamp(d) + pd.Timedelta(days=h)).date()),
            "forecast": pack(log_or_nan(np.where(mask, model[k], np.nan)), "log_chl"),
            "observed": pack(log_or_nan(obs), "log_chl"),
            "scored": int(sel.sum()),
            "coverage_pct": float(100 * sel.sum() / mask.sum()),
            **{f"log_rmse_{m}": float(np.sqrt(np.mean(e ** 2))) for m, e in log_err.items()},
            **{f"median_rel_err_{m}": float(np.median(np.abs(10 ** e - 1)) * 100) for m, e in log_err.items()},
            "bias_model": float(np.mean(model[k][sel] - target[k][sel])),
        }

    if h not in MAP_HORIZONS:
        continue

    # Per-pixel statistics over 2025
    target_month = (issue_dates + pd.Timedelta(days=h)).month
    winter = np.isin(target_month, list(WINTER))[:, None, None]
    sq_model = np.where(scored, (np.log10(model) - np.log10(target)) ** 2, np.nan)
    sq_damped = np.where(scored, (np.log10(damped) - np.log10(target)) ** 2, np.nan)
    n_all = scored.sum(axis=0)
    n_winter = (scored & winter).sum(axis=0)
    with np.errstate(all="ignore"):
        rmse_model = np.sqrt(np.nanmean(sq_model, axis=0))
        rmse_damped = np.sqrt(np.nanmean(sq_damped, axis=0))
        gain = 100 * (1 - rmse_model / rmse_damped)
        bias_winter = np.nanmean(np.where(scored & winter, model - target, np.nan), axis=0)
    rmse_model[n_all < MIN_PAIRS] = np.nan
    gain[n_all < MIN_PAIRS] = np.nan
    bias_winter[n_winter < MIN_PAIRS] = np.nan

    pixel_stats[h] = (np.where(mask, gain, np.nan), np.where(mask, rmse_model, np.nan))
    pixel_maps[h] = {
        "bias_winter": pack(bias_winter, "bias"),
        "log_rmse": pack(rmse_model, "log_rmse"),
        "gain_vs_blend": pack(gain, "gain"),
        "summary": {
            "pixels_beating_blend_pct": float(100 * np.mean(gain[np.isfinite(gain)] > 0)),
            "median_pixel_gain": float(np.nanmedian(gain)),
            "winter_bias_mean": float(np.nanmean(bias_winter)),
            "winter_bias_share_positive_pct": float(100 * np.mean(bias_winter[np.isfinite(bias_winter)] > 0)),
            "median_pairs_per_pixel": float(np.median(n_all[mask])),
            "median_winter_pairs_per_pixel": float(np.median(n_winter[mask])),
        },
    }

# Regional contrast: open channel versus the Sicilian coastal strip, +1 day.
lat = data.latitude.values[:, None] * np.ones((1, NX))
lon = np.ones((NY, 1)) * data.longitude.values[None, :]
coastal = mask & (lat > 36.6) & (lon > 14.4)
open_sea = mask & (lat > 35.6) & (lat < 36.5)
regions = {}
for h in MAP_HORIZONS:
    g, e = pixel_stats[h]
    regions[h] = {"coast_median_error": float(np.nanmedian(e[coastal])), "open_median_error": float(np.nanmedian(e[open_sea])),
                  "coast_median_gain": float(np.nanmedian(g[coastal])), "open_median_gain": float(np.nanmedian(g[open_sea]))}

OUT_PATH.write_text(json.dumps({
    "grid": {
        "latitude": [round(float(v), 5) for v in data.latitude.values],
        "longitude": [round(float(v), 5) for v in data.longitude.values],
        "sea": sea.astype(int).tolist(),
    },
    "examples": examples,
    "pixel_maps": pixel_maps,
    "regions": regions,
    "min_pairs": MIN_PAIRS,
}, separators=(",", ":")))

for h, saved, rerun in checks:
    print(f"+{h}d model log RMSE: saved {saved:.6f}, re-run {rerun:.6f}")
for d in EXAMPLE_DAYS:
    for h in [1, 4, 7]:
        e = examples[d][h]
        print(f"{d} +{h}d → {e['target_date']}: scored {e['scored']:,} ({e['coverage_pct']:.0f}%), "
              f"model {e['log_rmse_model']:.3f}, blend {e['log_rmse_damped']:.3f}, persistence {e['log_rmse_persistence']:.3f}")
for h in MAP_HORIZONS:
    print(f"+{h}d", pixel_maps[h]["summary"], regions[h])
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
