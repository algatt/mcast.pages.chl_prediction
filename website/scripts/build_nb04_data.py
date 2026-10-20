"""Build the data behind the Step 04 page (04-Forecast-Preparation.ipynb).

Reads the prepared file the notebook writes, plus the collated observations,
and saves website/src/data/nb04.json: the splits and their sample counts, the
quality-control counts, how old the latest observation is, wind measurement
ages, and one pixel followed through a few weeks with its inputs and targets
exactly as the notebook computed them.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb04_data.py
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiment_v2/data/processed"
PREPARED = DATA / "malta_forecast_prepared.nc"
COLLATED = DATA / "malta_daily_observations.nc"
OUT_PATH = ROOT / "website/src/data/nb04.json"

MAX_PLAUSIBLE_CHL = 10.0
MIN_TRAINING_OBSERVATIONS = 200
HORIZONS = (1, 4, 7)

# The example pixel and the window shown on the page.
PIXEL = (36.2, 14.5)
SERIES = ("2023-12-26", "2024-03-02")
ISSUE_DAYS = ("2024-01-08", "2024-02-20")

prepared = xr.open_dataset(PREPARED)
observations = xr.open_dataset(COLLATED)
dates = pd.DatetimeIndex(prepared.time.values)
mask = prepared["model_mask"].values == 1

# --- Splits -------------------------------------------------------------------
splits = []
for name in ["train", "validation", "test"]:
    in_split = prepared[f"split_{name}"].values == 1
    split_dates = dates[in_split]
    days = np.flatnonzero(in_split)
    block = slice(days[0], days[-1] + 1)          # contiguous read (fast)
    in_block = in_split[block]
    row = {"name": name, "first": str(split_dates[0].date()), "last": str(split_dates[-1].date()),
           "issue_days": int(in_split.sum()), "targets": {}}
    for h in HORIZONS:
        target = prepared[f"chl_target_{h}d"].isel(time=block).values[in_block]
        valid = np.isfinite(target) & mask[None]
        row["targets"][h] = {"count": int(valid.sum()),
                             "coverage_pct": float(100 * valid.sum() / (in_split.sum() * mask.sum()))}
    # How old the latest observation is, for +1-day targets.
    age = prepared["chl_age_days"].isel(time=block).values[in_block]
    target1 = prepared["chl_target_1d"].isel(time=block).values[in_block]
    ages = age[np.isfinite(target1) & mask[None]]
    row["age_pct"] = {
        "1": float(100 * np.mean(ages == 1)),
        "2": float(100 * np.mean(ages == 2)),
        "3": float(100 * np.mean(ages == 3)),
        "4–7": float(100 * np.mean((ages >= 4) & (ages <= 7))),
        "8+": float(100 * np.mean(ages >= 8)),
    }
    row["median_age"] = float(np.nanmedian(ages))
    splits.append(row)

# --- Quality control counts ----------------------------------------------------
chl = observations["chl"].values
too_high = int((chl > MAX_PLAUSIBLE_CHL).sum())
clean = np.where((chl > 0) & (chl <= MAX_PLAUSIBLE_CHL), chl, np.nan)
train_days = prepared["split_train"].values == 1
train_period = (dates >= pd.Timestamp("2017-01-01")) & (dates <= pd.Timestamp("2023-12-31"))
counts = np.isfinite(clean[train_period]).sum(axis=0)
qc = {
    "values_removed": too_high,
    "valid_values": int(np.isfinite(chl).sum()),
    "pixels_included": int(mask.sum()),
    "pixels_rarely_observed": int(((counts > 0) & (counts < MIN_TRAINING_OBSERVATIONS)).sum()),
    "grid_pixels": int(mask.size),
    "median_training_observations": float(np.median(counts[mask])),
}
assert qc["pixels_included"] == int((counts >= MIN_TRAINING_OBSERVATIONS).sum())

# --- Wind measurement ages at issue time -----------------------------------------
wind_age = {}
for p in ["asc", "des"]:
    v = prepared[f"wind_age_hours_{p}"].values
    wind_age[p] = [float(np.nanmin(v)), float(np.nanmedian(v)), float(np.nanmax(v))]

# --- Example pixel -------------------------------------------------------------
i = int(np.abs(prepared.latitude.values - PIXEL[0]).argmin())
j = int(np.abs(prepared.longitude.values - PIXEL[1]).argmin())
assert mask[i, j]
series_dates = pd.date_range(*SERIES, freq="D")
observed = observations["chl"].sel(time=series_dates).isel(latitude=i, longitude=j).values
observed = np.where((observed > 0) & (observed <= MAX_PLAUSIBLE_CHL), observed, np.nan)

issue_dates = pd.date_range(*ISSUE_DAYS, freq="D")
px = prepared.isel(latitude=i, longitude=j).sel(time=issue_dates)
issues = []
for k, day in enumerate(issue_dates):
    latest = float(px["chl_latest"].values[k])
    age = float(px["chl_age_days"].values[k])
    # The latest observation must be the observed value `age` days before the issue day.
    source_day = day - pd.Timedelta(days=int(age))
    assert np.isclose(observed[series_dates.get_loc(source_day)], latest, rtol=1e-6), day
    issues.append({
        "date": str(day.date()),
        "chl_latest": latest,
        "chl_age_days": int(age),
        "chl_mean_7d": float(px["chl_mean_7d"].values[k]) if np.isfinite(px["chl_mean_7d"].values[k]) else None,
        "chl_observations_7d": int(px["chl_observations_7d"].values[k]),
        "sst_c": float(px["sst_c"].values[k]) if np.isfinite(px["sst_c"].values[k]) else None,
        "clim": float(10 ** px["chl_clim_log"].values[k]),
        "targets": {h: (float(px[f"chl_target_{h}d"].values[k]) if np.isfinite(px[f"chl_target_{h}d"].values[k]) else None)
                    for h in HORIZONS},
    })

example = {
    "latitude": float(prepared.latitude.values[i]),
    "longitude": float(prepared.longitude.values[j]),
    "series": [{"date": str(d.date()), "chl": (float(v) if np.isfinite(v) else None)}
               for d, v in zip(series_dates, observed)],
    "issues": issues,
}

OUT_PATH.write_text(json.dumps({
    "splits": splits,
    "qc": qc,
    "wind_age_hours": wind_age,
    "training_period": prepared.attrs["training_period"],
    "feature_names": json.loads(prepared.attrs["feature_names_json"]),
    "example": example,
}, separators=(",", ":")))

print(json.dumps({"splits": splits, "qc": qc, "wind_age": wind_age}, indent=1))
print(f"Example pixel {example['latitude']:.3f}N {example['longitude']:.3f}E: "
      f"{sum(s['chl'] is not None for s in example['series'])} of {len(example['series'])} days observed")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
