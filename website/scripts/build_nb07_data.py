"""Build the data behind the Step 07 page (07-NRT-Input-Validation.ipynb).

Reads the most recent live (near-real-time) forecast the notebook saved, the
local NRT archive written by 08-NRT-Archive.ipynb, and the earlier batch check
from 7 October 2026 (made with the previous model), and saves
website/src/data/nb07.json.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb07_data.py
"""

from pathlib import Path
import base64
import json

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
FORECASTS = EXP / "data/processed/nrt_forecasts"
ARCHIVE = EXP / "data/raw/nrt_archive"
EARLIER = EXP / "data/processed/nrt_batch_evaluation/20261007T135242Z"
L4 = EXP / "data/chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
OUT_PATH = ROOT / "website/src/data/nb07.json"

with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)


def pack(field, lo, hi):
    """One byte per pixel over [lo, hi], 255 = no value; see src/data/packed.js."""
    ok = np.isfinite(field) & sea
    q = np.full(field.shape, 255, dtype=np.uint8)
    q[ok] = np.rint((np.clip(field[ok], lo, hi) - lo) / (hi - lo) * 254).astype(np.uint8)
    return {"range": [lo, hi], "data": base64.b64encode(q.tobytes()).decode("ascii")}


def log_or_nan(field):
    with np.errstate(all="ignore"):
        return np.where(field > 0, np.log10(field), np.nan)


# --- The most recent live forecast ------------------------------------------------
latest = sorted(p for p in FORECASTS.iterdir() if (p / "chl_forecasts.nc").exists())[-1]
forecast = xr.open_dataset(latest / "chl_forecasts.nc")
inputs = xr.open_dataset(latest / "nrt_features.nc")
mask = forecast["model_mask"].values == 1
history = forecast["chl_history_available"].values == 1
age = inputs["chl_age_days"].values

ages = age[mask & np.isfinite(age)]
live = {
    "run": latest.name,
    "issue_date": forecast.attrs["issue_date"],
    "issue_time_utc": forecast.attrs["nominal_issue_time_utc"],
    "retrieved_utc": forecast.attrs["retrieval_finished_utc"],
    "latest_chl_date": inputs.attrs["chl_latest_eligible_date"],
    "sst_date": inputs.attrs["sst_date"],
    "versions": json.loads(forecast.attrs["source_versions_json"]),
    "datasets": json.loads(forecast.attrs["source_datasets_json"]),
    "model_file": forecast.attrs["model_file"],
    "n_inputs": len(json.loads(forecast.attrs["feature_names_json"])),
    "pixels": int(mask.sum()),
    "pixels_with_history": int((mask & history).sum()),
    "pixels_with_sst": int((mask & (forecast["sst_available"].values == 1)).sum()),
    "age_counts": {str(int(a)): int((ages == a).sum()) for a in np.unique(ages)},
    "target_dates": [str(d)[:10] for d in forecast.target_date.values],
    "maps": {
        **{f"forecast_{int(h)}": pack(log_or_nan(np.where(mask, forecast["chl_forecast"].sel(horizon=h).values, np.nan)), -2.0, 1.0)
           for h in forecast.horizon.values},
        "latest": pack(log_or_nan(np.where(mask, inputs["chl_latest"].values, np.nan)), -2.0, 1.0),
        "age": pack(np.where(mask, age, np.nan), 0.0, 14.0),
        "sst": pack(np.where(mask, inputs["sst_c"].values, np.nan), 15.0, 30.0),
        "fallback": pack(np.where(mask & ~history, 1.0, np.where(mask, 0.0, np.nan)), 0.0, 1.0),
    },
}
sst_values = inputs["sst_c"].values[mask & np.isfinite(inputs["sst_c"].values)]
live["sst_range"] = [float(sst_values.min()), float(sst_values.max())]

# --- The local NRT archive ----------------------------------------------------------
archive = {}
for source in ["chl", "chl_l4", "sst"]:
    dates = sorted(p.stem for p in (ARCHIVE / source).glob("*.nc"))
    expected = pd.date_range(dates[0], dates[-1], freq="D").strftime("%Y-%m-%d")
    archive[source] = {"days": len(dates), "first": dates[0], "last": dates[-1],
                       "missing": sorted(set(expected) - set(dates))}
log = pd.read_csv(ARCHIVE / "archive_log.csv")
archive["runs"] = int(log["Retrieved (UTC)"].nunique())

# --- The earlier check, with the earlier model ---------------------------------------
earlier_rows = json.loads((EARLIER / "l3_shared_pixels.json").read_text())
provenance = json.loads((EARLIER / "provenance.json").read_text())
earlier = {
    "issue_dates": [provenance["issue_dates"][0], provenance["issue_dates"][-1]],
    "n_issue_dates": len(provenance["issue_dates"]),
    "features": len(provenance["features"]),
    "rows": [{"horizon": r["Horizon"], "history": r["Input history"], "method": r["Method"],
              "issue_dates": r["Scored issue dates"], "pixel_days": r["Scored pixel-days"],
              "log_rmse": r["RMSE (log10)"]} for r in earlier_rows],
}

OUT_PATH.write_text(json.dumps({
    "grid": {
        "latitude": [round(float(v), 5) for v in forecast.latitude.values],
        "longitude": [round(float(v), 5) for v in forecast.longitude.values],
        "sea": sea.astype(int).tolist(),
    },
    "live": live,
    "archive": archive,
    "earlier": earlier,
}, separators=(",", ":")))

print(json.dumps({k: v for k, v in live.items() if k != "maps"}, indent=1))
print(json.dumps(archive, indent=1))
print(f"Earlier check: {earlier['n_issue_dates']} issue dates, {earlier['features']} inputs")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
