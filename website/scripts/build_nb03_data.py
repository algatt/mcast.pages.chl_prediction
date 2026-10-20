"""Build the data behind the Step 03 page (03-Data-Exploration.ipynb).

Reads the collated file written by 02-Collate-and-Prepare.ipynb and saves
website/src/data/nb03.json: monthly observation coverage, gap lengths, the
seasonal cycle by era, seasonal median maps, how chlorophyll relates to
temperature and wind, and how quickly day-to-day similarity fades.

Chlorophyll above 10 mg/m³ is treated as missing, as in step 04.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb03_data.py
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiment_v2/data"
COLLATED = DATA / "processed/malta_daily_observations.nc"
L4 = DATA / "chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
OUT_PATH = ROOT / "website/src/data/nb03.json"

MAX_PLAUSIBLE_CHL = 10.0
ERA_SPLIT = 2017
MIN_DAILY_COVERAGE = 0.05      # regional daily medians need at least 5% of the sea observed
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]

with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)

data = xr.open_dataset(COLLATED)
dates = pd.DatetimeIndex(data.time.values)
chl = data["chl"].values
chl = np.where((chl > 0) & (chl <= MAX_PLAUSIBLE_CHL), chl, np.nan)
sst = data["sst_c"].values
wind = data["wind_speed_des"].values                    # morning pass

chl_sea = chl[:, sea]                                   # (days, sea pixels)
observed = np.isfinite(chl_sea)
n_sea = int(sea.sum())

# --- 1. Monthly coverage matrix ----------------------------------------------
daily_cov = pd.Series(100 * observed.mean(axis=1), index=dates)
sst_cov = pd.Series(100 * np.isfinite(sst[:, sea]).mean(axis=1), index=dates)


def matrix(series):
    m = series.groupby([series.index.year, series.index.month]).mean().unstack()
    return {str(year): [round(float(v), 1) for v in row] for year, row in m.iterrows()}


coverage = {"chl": matrix(daily_cov), "sst": matrix(sst_cov)}
month_cov = daily_cov.groupby(daily_cov.index.month).mean()

# --- 2. Gap lengths (bounded gaps only: observed before and after) -------------
missing = ~observed.T                                   # (pixels, days)
padded = np.pad(missing, ((0, 0), (1, 1)), constant_values=False).astype(np.int8)
changes = np.diff(padded, axis=1)
_, starts = np.nonzero(changes == 1)
_, ends = np.nonzero(changes == -1)
lengths = ends - starts
bounded = (starts > 0) & (ends < missing.shape[1])
lengths = lengths[bounded]
bins = [(1, 1, "1 day"), (2, 2, "2 days"), (3, 3, "3 days"), (4, 7, "4–7 days"),
        (8, 14, "1–2 weeks"), (15, 30, "2–4 weeks"), (31, 10**6, "over a month")]
gaps = [{
    "label": label,
    "events_pct": float(100 * ((lengths >= lo) & (lengths <= hi)).mean()),
    "missing_days_pct": float(100 * lengths[(lengths >= lo) & (lengths <= hi)].sum() / lengths.sum()),
} for lo, hi, label in bins]
gap_summary = {
    "events": int(lengths.size),
    "median_days": float(np.median(lengths)),
    "share_one_day_pct": gaps[0]["events_pct"],
    "share_over_week_missing_days_pct": float(100 * lengths[lengths >= 8].sum() / lengths.sum()),
}

# --- 3. Seasonal cycle by era --------------------------------------------------
enough = observed.mean(axis=1) >= MIN_DAILY_COVERAGE
daily_median = pd.Series(np.where(enough, np.nanmedian(np.where(observed, chl_sea, np.nan), axis=1), np.nan),
                         index=dates).dropna()
cycle = {}
for era, mask in [("2008–2016", daily_median.index.year < ERA_SPLIT),
                  ("2017–2025", daily_median.index.year >= ERA_SPLIT)]:
    s = daily_median[mask]
    g = s.groupby(s.index.month)
    cycle[era] = [{
        "month": int(m),
        "median": float(g.median()[m]),
        "q25": float(g.quantile(0.25)[m]),
        "q75": float(g.quantile(0.75)[m]),
        "days": int(g.size()[m]),
    } for m in range(1, 13)]

annual = {era: float(np.median([p["median"] for p in pts])) for era, pts in cycle.items()}

# --- 4. Seasonal median maps ---------------------------------------------------
season_of_day = np.array([SEASONS[m] for m in dates.month])
maps = {}
for season in SEASON_ORDER:
    with np.errstate(all="ignore"):
        med = np.nanmedian(chl[season_of_day == season], axis=0)
    out = np.full(med.shape, None, dtype=object)
    ok = np.isfinite(med) & sea
    out[ok] = np.rint(np.log10(med[ok]) * 1000).astype(int)
    maps[season] = out.tolist()

# --- 5. Chlorophyll against temperature and wind (daily regional medians) ------
def paired_daily(other):
    """Daily medians over pixels where both chlorophyll and `other` exist."""
    other_sea = other[:, sea]
    both = observed & np.isfinite(other_sea)
    ok = both.mean(axis=1) >= MIN_DAILY_COVERAGE
    c = np.nanmedian(np.where(both, chl_sea, np.nan)[ok], axis=1)
    o = np.nanmedian(np.where(both, other_sea, np.nan)[ok], axis=1)
    return pd.DataFrame({"chl": c, "other": o, "season": season_of_day[ok]}, index=dates[ok])


def binned(frame, edges):
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = frame.loc[(frame["other"] >= lo) & (frame["other"] < hi), "chl"]
        if len(s) >= 15:
            rows.append({"x": float((lo + hi) / 2), "median": float(s.median()),
                         "q25": float(s.quantile(0.25)), "q75": float(s.quantile(0.75)), "days": int(len(s))})
    return rows


def spearman(a, b):
    return float(pd.Series(a).rank().corr(pd.Series(b).rank()))


def correlations(frame):
    out = {"all": spearman(frame["chl"], frame["other"])}
    for season in SEASON_ORDER:
        f = frame[frame["season"] == season]
        out[season] = spearman(f["chl"], f["other"])
    return out


sst_daily = paired_daily(sst)
wind_daily = paired_daily(wind)
relations = {
    "sst": {"bins": binned(sst_daily, np.arange(13, 31.5, 1.0)), "spearman": correlations(sst_daily),
            "days": int(len(sst_daily))},
    "wind": {"bins": binned(wind_daily, np.arange(0, 14.5, 1.0)), "spearman": correlations(wind_daily),
             "days": int(len(wind_daily))},
}

# --- 6. How fast day-to-day similarity fades, by season -------------------------
log_chl = np.log10(chl_sea)
fading = {season: [] for season in SEASON_ORDER}
for k in range(1, 8):
    diff = log_chl[k:] - log_chl[:-k]
    ok = np.isfinite(diff)
    start_season = season_of_day[:-k]
    for season in SEASON_ORDER:
        sel = ok & (start_season == season)[:, None]
        rmse = float(np.sqrt(np.mean(diff[sel] ** 2)))
        fading[season].append({"lag": k, "rmse_log10": rmse, "pairs": int(sel.sum())})

# Share of observed pixels that are observed again k days later.
reobserved = [{"lag": k, "pct": float(100 * (observed[k:] & observed[:-k]).sum() / observed[:-k].sum())}
              for k in range(1, 8)]

example = {
    "latitude": [round(float(v), 5) for v in data.latitude.values],
    "longitude": [round(float(v), 5) for v in data.longitude.values],
    "sea": sea.astype(int).tolist(),
}

OUT_PATH.write_text(json.dumps({
    "sea_pixels": n_sea,
    "period": [str(dates[0].date()), str(dates[-1].date())],
    "coverage_matrix_pct": coverage,
    "coverage_by_month_pct": [float(month_cov[m]) for m in range(1, 13)],
    "gaps": gaps,
    "gap_summary": gap_summary,
    "cycle": cycle,
    "cycle_annual_median": annual,
    "season_maps_log1000": maps,
    "relations": relations,
    "fading": fading,
    "reobserved": reobserved,
    "grid": example,
}, separators=(",", ":")))

print("coverage by month:", [round(v) for v in month_cov.values])
print("gap summary:", gap_summary)
for g in gaps: print(f"  {g['label']:>12}: {g['events_pct']:5.1f}% of gaps, {g['missing_days_pct']:5.1f}% of missing days")
for era, pts in cycle.items(): print(era, [round(p['median'], 3) for p in pts], "annual", round(annual[era], 3))
for k in ("sst", "wind"): print(k, relations[k]["days"], {s: round(v, 2) for s, v in relations[k]["spearman"].items()})
print("sst bins", [(b['x'], round(b['median'], 3)) for b in relations['sst']['bins']])
print("wind bins", [(b['x'], round(b['median'], 3), b['days']) for b in relations['wind']['bins']])
for s in SEASON_ORDER: print(s, [round(p['rmse_log10'], 3) for p in fading[s]])
print("reobserved", [round(r['pct']) for r in reobserved])
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
