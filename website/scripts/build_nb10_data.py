"""Build the data behind the Step 10 page (10-Bloom-Prediction.ipynb).

Sources, in order of preference:
  * the saved bloom model (models/bloom_step10.joblib): bloom counts, screening on
    2024, the 2025 test scores with 95% ranges, warnings, breakdowns, reliability;
  * a re-run on the observations: bloom share by year and season, the area-wide
    bloom share over time, and one example day's bloom probability map. The re-run
    of the 2025 test is checked against the saved Brier scores first.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb10_data.py
"""

from pathlib import Path
import base64
import json
import sys

import joblib
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
sys.path.insert(0, str(EXP))
from chlforecast import blooms, config  # noqa: E402
from chlforecast import features as F  # noqa: E402

L4 = EXP / "data/chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
OUT_PATH = ROOT / "website/src/data/nb10.json"
HISTORY_START = "2016-12-01"
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
EXAMPLE_HORIZON = 1
EXAMPLE_LATER_DAYS = 3          # the second example: the same event, three days on

bloom_model = joblib.load(config.BLOOM_MODEL_PATH)
in_use = joblib.load(config.MODEL_PATH)
if not bloom_model["method"].startswith("Classifier"):
    sys.exit("This page expects the classifier to have won the 2024 screening; update the script.")
horizons = [int(h) for h in in_use["forecast_horizons_days"]]
names = bloom_model["feature_names"]

# --- Inputs, as in the notebook -------------------------------------------------------
with xr.open_dataset(config.PROCESSED / "malta_daily_observations.nc") as observations:
    observations = observations.sel(time=slice(HISTORY_START, None)).load()
dates = pd.DatetimeIndex(observations.time.values)
latitude, longitude = observations.latitude.values, observations.longitude.values
GRID = ("time", "latitude", "longitude")
chl = F.quality_control(observations["chl"].transpose(*GRID).values, minimum=config.MIN_PLAUSIBLE_CHL)
sst = observations["sst_c"].transpose(*GRID).values
with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)

mask = in_use["model_mask"].values == 1
monthly_log_clim = in_use["monthly_log_climatology"].values
inputs = F.model_inputs(chl, sst, dates, mask, monthly_log_clim, in_use["monthly_sst_climatology"].values,
                        in_use["coast_distance_km"].values, latitude, longitude)
area_state = blooms.area_state_inputs(chl, dates, mask, monthly_log_clim)
inputs.update(area_state)

# --- Blooms by year and season, on observation days -----------------------------------
with np.errstate(divide="ignore", invalid="ignore"):
    anomaly = np.log10(chl) - F.climatology_for_dates(monthly_log_clim, dates)
observed = np.isfinite(anomaly) & mask[None]
season_of = np.array([SEASONS[m] for m in dates.month])
season_year = np.where(dates.month == 12, dates.year + 1, dates.year)        # December counts with the next winter
by_season = []
for year in range(2017, 2026):
    for season in ["Winter", "Spring", "Summer", "Autumn"]:
        days = (season_year == year) & (season_of == season)
        if season == "Winter" and year == 2017:
            days &= dates >= pd.Timestamp("2017-01-01")                     # training starts in January 2017
        sel = observed & days[:, None, None]
        by_season.append({"year": year, "season": season, "n": int(sel.sum()),
                          "bloom_pct": float(100 * np.mean(anomaly[sel] >= config.BLOOM_ANOMALY_LOG10))})
by_year = []
for year in range(2017, 2026):
    sel = observed & (dates.year == year)[:, None, None]
    by_year.append({"year": year, "bloom_pct": float(100 * np.mean(anomaly[sel] >= config.BLOOM_ANOMALY_LOG10))})

share = pd.Series(area_state["area_bloom_share_30d"][:, 0, 0], index=dates)
weekly = share["2017-01-01":"2025-12-31"].resample("W-SUN").last().dropna()
area_series = [{"date": d.strftime("%Y-%m-%d"), "share_pct": round(float(100 * v), 2)} for d, v in weekly.items()]

def make_example(k, h, t, i, j, bloom, probs):
    """Bloom probability maps for issue day k, and what was then observed."""
    on_day = t == k
    prob_map = np.full(mask.shape, np.nan)
    rule_map = np.full(mask.shape, np.nan)
    obs_map = np.full(mask.shape, np.nan)
    # Probabilities are shown for every modelled pixel, observed or not.
    Xd = pd.DataFrame({n: np.broadcast_to(inputs[n], chl.shape)[k][mask] for n in names}).astype("float32")
    prob_map[mask] = bloom_model["models"][h].predict_proba(Xd)[:, 1]
    rule_map[mask] = blooms.anomaly_rule(bloom_model["anomaly_rule"][h],
                                         np.asarray(inputs["chl_anomaly_log"])[k][mask].astype("float64"), bins)
    obs_map[i[on_day], j[on_day]] = bloom[on_day]
    b, pm, pr = bloom[on_day], probs["Bloom model"][on_day], probs["Anomaly rule"][on_day]
    return {"issue_date": dates[k].strftime("%Y-%m-%d"),
            "target_date": (dates[k] + pd.Timedelta(days=h)).strftime("%Y-%m-%d"),
            "horizon": h, "observed_pixels": int(on_day.sum()), "bloom_pixels": int(b.sum()),
            "maps": {"probability": prob_map, "rule": rule_map, "observed": obs_map},
            "brier_model": blooms.brier(pm, b), "brier_rule": blooms.brier(pr, b),
            "mean_prob_on_blooms": float(pm[b == 1].mean()), "mean_prob_elsewhere": float(pm[b == 0].mean()),
            "rule_prob_on_blooms": float(pr[b == 1].mean())}


# --- Re-run of the 2025 test, and the example day ---------------------------------------
last_target = dates + pd.Timedelta(days=max(horizons))
test_start, test_end = config.SPLIT_PERIODS["test"]
in_test = (dates >= pd.Timestamp(test_start)) & (last_target <= pd.Timestamp(test_end))
saved = {(int(r["Horizon"][1:-1]), r["Method"]): r for r in bloom_model["test_scores"]}
bins = bloom_model["anomaly_bins"]
checks, examples = [], None
for h in horizons:
    target = np.full(chl.shape, np.nan, dtype="float32")
    target[:-h] = chl[h:]
    target_clim = F.climatology_for_dates(monthly_log_clim, dates + pd.Timedelta(days=h))
    valid = np.isfinite(target) & (target > 0) & mask[None] & in_test[:, None, None]
    t, i, j = np.nonzero(valid)
    X = pd.DataFrame({n: np.broadcast_to(inputs[n], chl.shape)[t, i, j] for n in names}).astype("float32")
    bloom = blooms.is_bloom(target[t, i, j].astype("float64"), target_clim[t, i, j].astype("float64"))
    months = (dates[t] + pd.Timedelta(days=h)).month.to_numpy()
    probs = {
        "Bloom model": bloom_model["models"][h].predict_proba(X)[:, 1],
        "Anomaly rule": blooms.anomaly_rule(bloom_model["anomaly_rule"][h],
                                            np.asarray(inputs["chl_anomaly_log"])[t, i, j].astype("float64"), bins),
        "Usual frequency": bloom_model["usual_frequency"][h][months - 1, i, j],
    }
    for method, p in probs.items():
        checks.append((h, method, saved[(h, method)]["Brier score"], blooms.brier(p, bloom)))

    if h == EXAMPLE_HORIZON:
        # The test day whose target had the most observed bloom pixels, among days at least half observed.
        n_obs = np.bincount(t, minlength=len(dates))
        n_bloom = np.bincount(t, weights=bloom, minlength=len(dates))
        eligible = n_obs >= 0.5 * mask.sum()
        first = int(np.argmax(np.where(eligible, n_bloom, -1)))
        examples = [make_example(k, h, t, i, j, bloom, probs) for k in (first, first + EXAMPLE_LATER_DAYS)]
    print(f"+{h}d re-run done: {bloom.size:,} pixel-days")

failed = [c for c in checks if abs(c[2] - c[3]) > 1e-9]
for h, method, s, r in checks:
    print(f"  {'FAIL' if (h, method, s, r) in failed else 'ok  '} +{h}d {method:<16} Brier saved {s:.6f} re-run {r:.6f}")
if failed:
    sys.exit("The re-run does not reproduce the saved test scores: the data and the model are out of step.")


def pack(field, lo, hi):
    """One byte per pixel over [lo, hi], 255 = no value; see src/data/packed.js."""
    ok = np.isfinite(field) & sea
    q = np.full(field.shape, 255, dtype=np.uint8)
    q[ok] = np.rint((np.clip(field[ok], lo, hi) - lo) / (hi - lo) * 254).astype(np.uint8)
    return {"range": [lo, hi], "data": base64.b64encode(q.tobytes()).decode("ascii")}


for example in examples:
    example["maps"] = {k: pack(v, 0.0, 1.0) for k, v in example["maps"].items()}


def records(rows, rename):
    return [{rename.get(k, k): (int(v[1:-1]) if k == "Horizon" else v) for k, v in r.items()} for r in rows]


R = {"Horizon": "horizon", "Method": "method", "Brier score": "brier", "Skill vs usual frequency (%)": "skill",
     "95% low": "low", "95% high": "high", "Skill vs anomaly rule (%)": "skill_rule", "vs rule 95% low": "rule_low",
     "vs rule 95% high": "rule_high", "AUC": "auc", "Group": "group", "Pixel-days": "n", "Blooms": "blooms",
     "Threshold": "threshold", "Warnings": "warnings", "Hit rate (%)": "hit_rate", "False alarm ratio (%)": "false_alarm_ratio",
     "Critical success index (%)": "csi", "Period": "period", "Observed pixel-days": "n", "Bloom pixel-days": "blooms",
     "Bloom share (%)": "bloom_pct", "From": "from", "To": "to", "Forecasts": "n", "Mean probability": "mean_prob",
     "Observed frequency": "observed_freq"}

OUT_PATH.write_text(json.dumps({
    "grid": {
        "latitude": [round(float(v), 5) for v in latitude],
        "longitude": [round(float(v), 5) for v in longitude],
        "sea": sea.astype(int).tolist(),
    },
    "bloom_anomaly_log10": bloom_model["bloom_anomaly_log10"],
    "counts": records(bloom_model["bloom_counts"], R),
    "by_season": by_season,
    "by_year": by_year,
    "area_series": area_series,
    "screening": records(bloom_model["screening"], R),
    "test": records(bloom_model["test_scores"], R),
    "warnings": records(bloom_model["warnings"], R),
    "breakdown": records(bloom_model["breakdown"], R),
    "reliability": records(bloom_model["reliability"], R),
    "examples": examples,
    "n_inputs": len(names),
}, separators=(",", ":")))

for example in examples:
    print(json.dumps({k: v for k, v in example.items() if k != "maps"}))
print("Bloom share by year:", {r["year"]: round(r["bloom_pct"], 1) for r in by_year})
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
