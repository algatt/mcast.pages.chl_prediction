"""Build the data behind the Notebook 01 page.

Reads the CHL files downloaded by experiment_v2/01-Data Acquisition.ipynb and
writes website/src/data/nb01.json: one example day of L3 and L4 CHL on the
1 km grid, plus the L3-versus-L4 comparison over 2022–2025.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb01_data.py
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
CHL_DIR = ROOT / "experiment_v2/data/chl_l3_l4_comparison"
REGION = "13.9_15.2_35.55_36.9"
L3_PATH = CHL_DIR / f"chl_L3_2008-01-01_2025-12-31_{REGION}.nc"
L4_PATH = CHL_DIR / f"chl_L4_2022-01-01_2025-12-31_{REGION}.nc"
OUT_PATH = ROOT / "website/src/data/nb01.json"

# Example-day search window and target L3 coverage: a day with real cloud
# gaps, but enough observations to show the spatial pattern.
SEARCH = ("2023-01-01", "2024-05-31")
COVERAGE_RANGE = (0.45, 0.65)


def load_chl(path):
    with xr.open_dataset(path) as ds:
        chl = ds["CHL"].load()
    days = pd.DatetimeIndex(chl.time.values).normalize()
    chl = chl.assign_coords(time=days).sortby("time").sortby("latitude").sortby("longitude")
    return chl.transpose("time", "latitude", "longitude")


l3_all = load_chl(L3_PATH)
l4 = load_chl(L4_PATH)
l3 = l3_all.sel(time=l4.time)
l3, l4 = xr.align(l3, l4, join="exact")

valid3 = np.isfinite(l3.values) & (l3.values > 0)
valid4 = np.isfinite(l4.values) & (l4.values > 0)

# Sea pixels: L4 is gap-free over the sea, so pixels it never fills are land.
sea = valid4.any(axis=0)

overlap = valid3 & valid4
values3 = l3.values[overlap]
values4 = l4.values[overlap]
changed = values3 != values4

comparison = {
    "period": [str(l4.time.values[0])[:10], str(l4.time.values[-1])[:10]],
    "days": int(l4.sizes["time"]),
    "sea_pixels": int(sea.sum()),
    "valid_both": int(overlap.sum()),
    "valid_l3_missing_l4": int((valid3 & ~valid4).sum()),
    "filled_by_l4": int((~valid3 & valid4).sum()),
    "exactly_equal_pct": float(100 * np.mean(~changed)),
    "changed_mae": float(np.mean(np.abs(values4[changed] - values3[changed]))),
    "l3_share_of_sea_pixel_days_pct": float(100 * valid3[:, sea].mean()),
}

# Pick the example day: coverage in range, then the widest CHL range in L4.
window = (l4.time >= np.datetime64(SEARCH[0])) & (l4.time <= np.datetime64(SEARCH[1]))
candidates = []
for t in np.flatnonzero(window.values):
    coverage = valid3[t][sea].mean()
    if COVERAGE_RANGE[0] <= coverage <= COVERAGE_RANGE[1]:
        logs = np.log10(l4.values[t][sea])
        spread = float(np.nanpercentile(logs, 95) - np.nanpercentile(logs, 5))
        candidates.append((spread, t, coverage))
spread, day_index, day_coverage = max(candidates)
day = pd.Timestamp(l4.time.values[day_index])


def encode(field):
    """log10(CHL) × 1000 as integers; null where missing. Row 0 = southernmost."""
    out = np.full(field.shape, None, dtype=object)
    ok = np.isfinite(field) & (field > 0)
    out[ok] = np.rint(np.log10(field[ok]) * 1000).astype(int)
    return out.tolist()


example = {
    "date": f"{day:%Y-%m-%d}",
    "l3_coverage_pct": float(100 * day_coverage),
    "latitude": [round(float(v), 5) for v in l3.latitude.values],
    "longitude": [round(float(v), 5) for v in l3.longitude.values],
    "sea": sea.astype(int).tolist(),
    "l3_log1000": encode(l3.values[day_index]),
    "l4_log1000": encode(l4.values[day_index]),
}

# Share of all sea pixel-days 2008–2025 with a valid L3 value, per year.
valid_all = np.isfinite(l3_all.values) & (l3_all.values > 0)
years = pd.DatetimeIndex(l3_all.time.values).year
l3_coverage_by_year = {
    int(year): float(100 * valid_all[years == year][:, sea].mean())
    for year in np.unique(years)
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps({
    "comparison": comparison,
    "example": example,
    "l3_coverage_by_year_pct": l3_coverage_by_year,
}, separators=(",", ":")))

print(f"Example day {example['date']}: L3 covers {example['l3_coverage_pct']:.1f}% of the sea")
print(json.dumps(comparison, indent=2))
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
