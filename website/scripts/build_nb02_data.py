"""Build the data behind the Step 02 page (02-Collate-and-Prepare.ipynb).

Reads the raw downloads and the collated file the notebook writes, and saves
website/src/data/nb02.json: native grid sizes, the wind quality-flag counts,
satellite pass times, one example day of CHL, SST and wind on the 1 km grid,
and coverage statistics.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb02_data.py
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiment_v2/data"
REGION = "13.9_15.2_35.55_36.9"
RAW = {
    "sst": DATA / f"raw/sst_my_202511_2008-01-01_2025-12-31_{REGION}.nc",
    "wind_asc": DATA / f"raw/wind_ascending_my_202311_2019-01-01_2025-12-31_{REGION}.nc",
    "wind_des": DATA / f"raw/wind_descending_my_202311_2019-01-01_2025-12-31_{REGION}.nc",
    "l4": DATA / f"chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_{REGION}.nc",
}
COLLATED = DATA / "processed/malta_daily_observations.nc"
OUT_PATH = ROOT / "website/src/data/nb02.json"

# The same rejection list as NB02.
REJECT_FLAGS = {
    "distance_to_gmf_too_large",
    "wind_inversion_not_successful",
    "variational_quality_control_fails",
    "knmi_quality_control_fails",
    "product_monitoring_event_flag",
    "not_enough_good_sigma0_for_wind_retrieval",
}
FLAG_LABELS = {
    "some_portion_of_wvc_is_over_land": "Cell partly over land",
    "small_wind_less_than_or_equal_to_3_m_s": "Light wind (≤ 3 m/s)",
    "not_enough_good_sigma0_for_wind_retrieval": "Too few good radar returns",
    "knmi_quality_control_fails": "Failed KNMI quality control",
    "any_beam_noise_content_above_threshold": "Noisy radar beam",
    "variational_quality_control_fails": "Failed variational quality control",
    "distance_to_gmf_too_large": "Poor fit to the wind model",
    "wind_inversion_not_successful": "Wind retrieval failed",
    "large_wind_greater_than_30_m_s": "Strong wind (> 30 m/s)",
    "product_monitoring_event_flag": "Product monitoring event",
}

# Example-day search: good coverage in all three sources at once.
SEARCH = ("2023-01-01", "2024-12-31")


def spacing(values):
    return float(np.median(np.abs(np.diff(values))))


def lat_lon(ds):
    lat = ds["latitude"] if "latitude" in ds.coords else ds["lat"]
    lon = ds["longitude"] if "longitude" in ds.coords else ds["lon"]
    return np.sort(lat.values), np.sort(lon.values)


collated = xr.open_dataset(COLLATED)
chl_lat, chl_lon = collated.latitude.values, collated.longitude.values

# --- Native grids ---------------------------------------------------------
grids = {"chl": {
    "cells": [len(chl_lat), len(chl_lon)],
    "spacing_deg": [spacing(chl_lat), spacing(chl_lon)],
}}
native_centres = {}
for name, key in [("sst", "sst"), ("wind", "wind_des")]:
    with xr.open_dataset(RAW[key]) as ds:
        lat, lon = lat_lon(ds)
    grids[name] = {"cells": [len(lat), len(lon)], "spacing_deg": [spacing(lat), spacing(lon)]}
    native_centres[name] = {"latitude": lat.round(4).tolist(), "longitude": lon.round(4).tolist()}

# --- Wind quality flags (both passes together) ----------------------------
flag_counts = {}
total_available = 0
retention = {}
pass_hours = {}
for key, label in [("wind_asc", "ascending"), ("wind_des", "descending")]:
    with xr.open_dataset(RAW[key]) as ds:
        flags = ds["wvc_quality_flag"].load()
        speed = ds["wind_speed"].load()
        u = ds["eastward_wind"].load()
        v = ds["northward_wind"].load()
        times = ds["measurement_time"].load()
    meanings = flags.attrs["flag_meanings"].split()
    masks = [int(m) for m in flags.attrs["flag_masks"]]
    values = flags.fillna(0).astype("int64").values
    available = flags.notnull().values & np.isfinite(speed.values)
    total_available += int(available.sum())

    reject_mask = 0
    for meaning, mask in zip(meanings, masks):
        count = int((available & ((values & mask) != 0)).sum())
        flag_counts[meaning] = flag_counts.get(meaning, 0) + count
        if meaning in REJECT_FLAGS:
            reject_mask |= mask

    kept = (
        available & ((values & reject_mask) == 0)
        & np.isfinite(u.values) & np.isfinite(v.values) & (speed.values >= 0)
    )
    retention[label] = {"before": int(available.sum()), "kept": int(kept.sum())}

    labels = times.time.values.astype("datetime64[D]")[:, None, None]
    hours = (times.values - labels) / np.timedelta64(1, "h")
    hours = hours[kept & np.isfinite(hours)]
    pass_hours[label] = [float(np.min(hours)), float(np.median(hours)), float(np.max(hours))]

flags_out = [
    {
        "flag": f,
        "label": FLAG_LABELS.get(f, f.replace("_", " ")),
        "pct": 100 * c / total_available,
        "rejected": f in REJECT_FLAGS,
    }
    for f, c in sorted(flag_counts.items(), key=lambda kv: -kv[1])
    if c > 0
]

# --- Sea mask (as on the Step 01 page: pixels the gap-filled product fills) --
with xr.open_dataset(RAW["l4"]) as ds:
    l4 = ds["CHL"].load().sortby("latitude").sortby("longitude")
sea = np.isfinite(l4.values).any(axis=0)
assert np.allclose(l4.latitude.values, chl_lat) and np.allclose(l4.longitude.values, chl_lon)

# --- Example day --------------------------------------------------------------
window = collated.sel(time=slice(*SEARCH))
chl_ok = np.isfinite(window["chl"].values)
sst_ok = np.isfinite(window["sst_c"].values)
wind_ok = np.isfinite(window["wind_speed_des"].values)
n_sea = sea.sum()
cov = {
    "chl": chl_ok[:, sea].sum(axis=1) / n_sea,
    "sst": sst_ok[:, sea].sum(axis=1) / n_sea,
    "wind": wind_ok[:, sea].sum(axis=1) / n_sea,
}
score = np.minimum.reduce([cov["chl"] / 0.6, cov["sst"] / 0.9, cov["wind"] / 0.7])
t = int(np.argmax(score))
day = window.isel(time=t)


def encode(field, scale, log=False):
    out = np.full(field.shape, None, dtype=object)
    ok = np.isfinite(field) & sea
    if log:
        ok &= field > 0
        out[ok] = np.rint(np.log10(field[ok]) * scale).astype(int)
    else:
        out[ok] = np.rint(field[ok] * scale).astype(int)
    return out.tolist()


wind_times = day["wind_time_des"].values
valid_times = wind_times[~np.isnat(wind_times) & sea]
example = {
    "date": str(day.time.values)[:10],
    "coverage_pct": {k: float(100 * v[t]) for k, v in cov.items()},
    "wind_pass_utc": pd.Timestamp(valid_times.min()).strftime("%H:%M") if valid_times.size else None,
    "latitude": [round(float(v), 5) for v in chl_lat],
    "longitude": [round(float(v), 5) for v in chl_lon],
    "sea": sea.astype(int).tolist(),
    "chl_log1000": encode(day["chl"].values, 1000, log=True),
    "sst_c100": encode(day["sst_c"].values, 100),
    "wind_ms100": encode(day["wind_speed_des"].values, 100),
}

# --- Coverage over the full record -------------------------------------------
times = pd.DatetimeIndex(collated.time.values)
wind_period = times >= pd.Timestamp("2019-01-01")
coverage = []
for name, var, period in [
    ("Chlorophyll", "chl", slice(None)),
    ("Sea temperature", "sst_c", slice(None)),
    ("Wind, morning pass", "wind_speed_des", wind_period),
    ("Wind, evening pass", "wind_speed_asc", wind_period),
]:
    values = collated[var].values[period]
    ok = np.isfinite(values) & sea
    coverage.append({
        "name": name,
        "period": [str(times[period][0].year), str(times[period][-1].year)],
        "days": int(values.shape[0]),
        "days_with_data": int(ok.any(axis=(1, 2)).sum()),
        "sea_pixel_days_pct": float(100 * ok[:, sea].mean()),
    })

chl_valid = np.isfinite(collated["chl"].values) & sea
sst_valid = np.isfinite(collated["sst_c"].values)
wind_any = np.isfinite(collated["wind_speed_asc"].values) | np.isfinite(collated["wind_speed_des"].values)
recent = wind_period[:, None, None]
together = {
    "chl_with_sst_pct": float(100 * (chl_valid & sst_valid).sum() / chl_valid.sum()),
    "chl_with_wind_since_2019_pct": float(
        100 * (chl_valid & wind_any & recent).sum() / (chl_valid & recent).sum()
    ),
    "chl_with_all_since_2019_pct": float(
        100 * (chl_valid & sst_valid & wind_any & recent).sum() / (chl_valid & recent).sum()
    ),
}

ranges = {
    "chl_max_mg_m3": float(np.nanmax(collated["chl"].values)),
    "sst_c": [float(np.nanmin(collated["sst_c"].values)), float(np.nanmax(collated["sst_c"].values))],
}

OUT_PATH.write_text(json.dumps({
    "grids": grids,
    "native_centres": native_centres,
    "wind_flags": flags_out,
    "wind_retention": retention,
    "wind_pass_hours_utc": pass_hours,
    "example": example,
    "coverage": coverage,
    "together": together,
    "ranges": ranges,
    "file_mb": COLLATED.stat().st_size / 1e6,
}, separators=(",", ":")))

print(f"Example day {example['date']}: coverage {example['coverage_pct']}, wind pass {example['wind_pass_utc']}")
print(json.dumps({"grids": grids, "retention": retention, "pass_hours": pass_hours,
                  "coverage": coverage, "together": together, "ranges": ranges}, indent=1))
for f in flags_out:
    print(f"  {f['pct']:6.2f}%  {'REJECT' if f['rejected'] else 'keep  '}  {f['label']}")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
