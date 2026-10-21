"""Build the data behind the Step 09 page (09-Model-Improvements.ipynb).

Sources, in order of preference:
  * the model in use (models/chl_forecast_step09.joblib, promoted from the step 09
    candidate): screening on 2024, the 2025 test scores and 95% ranges, settings;
  * the tuning and coast/offshore tables recorded in the notebook's outputs;
  * a re-run on the 2025 test rows of the new model, the step 05 model and the
    blend rule, for breakdowns by season and on high-chlorophyll days, and for
    per-pixel maps. The re-run is checked against the saved test scores first.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb09_data.py
"""

from pathlib import Path
import base64
import html
import json
import re
import sys

import joblib
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
sys.path.insert(0, str(EXP))
from chlforecast import baselines, config  # noqa: E402
from chlforecast import features as F  # noqa: E402

NOTEBOOK = EXP / "09-Model-Improvements.ipynb"
L4 = EXP / "data/chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
OUT_PATH = ROOT / "website/src/data/nb09.json"

HISTORY_START = "2016-12-01"
HIGH_ANOMALY_LOG10 = 0.2          # as in step 05: at least 1.6 × the monthly normal
COAST_KM = 5                      # as in the notebook's coast/offshore table
MIN_PAIRS = 30                    # per pixel, for the maps (as in step 06)
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}

bundle = joblib.load(config.MODEL_PATH)
step05 = joblib.load(config.STEP05_MODEL_PATH)
horizons = [int(h) for h in bundle["forecast_horizons_days"]]


# --- Tables from the notebook's outputs --------------------------------------------------
def notebook_tables(cell_marker):
    """The HTML tables displayed by the code cell whose source contains `cell_marker`."""
    nb = json.loads(NOTEBOOK.read_text())
    cell = next(c for c in nb["cells"] if c["cell_type"] == "code" and cell_marker in "".join(c["source"]))
    tables = []
    for output in cell.get("outputs", []):
        markup = "".join(output.get("data", {}).get("text/html", ""))
        if not markup:
            continue
        rows = [[html.unescape(re.sub(r"<.*?>", "", x)).strip() for x in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)]
                for row in re.findall(r"<tr>(.*?)</tr>", markup, re.S)]
        tables.append(rows[2:])          # drop the two header rows
    if not tables:
        sys.exit(f"No saved outputs for the cell containing {cell_marker!r}: re-run and save the notebook.")
    return tables


def with_horizon(rows):
    """Rows of a two-level table, where the horizon is only written on its first row."""
    out, horizon = [], None
    for row in rows:
        if row[0].startswith("+") and row[0].endswith("d") and len(row) > 1 and not row[0][1:-1].startswith("."):
            horizon, row = int(row[0][1:-1]), row[1:]
        out.append([horizon, *row])
    return out


number = lambda s: float(s.replace(",", "").replace("+", ""))  # noqa: E731

tuning = [{"horizon": h, "settings": int(k), "learning_rate": number(lr), "max_iter": int(number(it)),
           "max_leaf_nodes": int(number(leaves)), "min_samples_leaf": int(number(leaf)),
           "gain": number(g), "low": number(lo), "high": number(hi)}
          for h, k, lr, it, leaves, leaf, g, lo, hi in with_horizon(notebook_tables("GRID_SEARCH = [")[0])]
area_notebook = [{"horizon": h, "area": area, "n": int(number(n)), "new": number(a), "step05": number(b), "blend": number(c)}
                 for h, area, n, a, b, c in with_horizon(notebook_tables("near_coast =")[2])]

# --- Re-run on 2025 -----------------------------------------------------------------------
with xr.open_dataset(config.PROCESSED / "malta_daily_observations.nc") as observations:
    observations = observations.sel(time=slice(HISTORY_START, None)).load()
dates = pd.DatetimeIndex(observations.time.values)
latitude, longitude = observations.latitude.values, observations.longitude.values
GRID = ("time", "latitude", "longitude")
raw_chl = observations["chl"].transpose(*GRID).values
chl = F.quality_control(raw_chl, minimum=config.MIN_PLAUSIBLE_CHL)
removed_by_lower_bound = int(np.isfinite(F.quality_control(raw_chl)).sum() - np.isfinite(chl).sum())
del raw_chl
sst = observations["sst_c"].transpose(*GRID).values
with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(axis=0)

mask = bundle["model_mask"].values == 1
monthly_log_clim = bundle["monthly_log_climatology"].values
coast_km = bundle["coast_distance_km"].values
inputs = F.model_inputs(chl, sst, dates, mask, monthly_log_clim, bundle["monthly_sst_climatology"].values,
                        coast_km, latitude, longitude)

# Missing share of each new input over the training issue days (as in the notebook).
train_start, train_end = config.SPLIT_PERIODS["train"]
in_train = (dates >= pd.Timestamp(train_start)) & (dates + pd.Timedelta(days=max(horizons)) <= pd.Timestamp(train_end))
missing = {name: float(100 * np.isnan(np.broadcast_to(inputs[name], chl.shape)[in_train][:, mask]).mean())
           for name in config.EXTRA_FEATURES}

test_start, test_end = config.SPLIT_PERIODS["test"]
in_test = (dates >= pd.Timestamp(test_start)) & (dates + pd.Timedelta(days=max(horizons)) <= pd.Timestamp(test_end))


def saved_score(method, h):
    return next(r for r in bundle["test_scores"] if r["Horizon"] == f"+{h}d" and r["Method"] == method)


def pack(field, lo, hi):
    """One byte per pixel over [lo, hi], 255 = no value; see src/data/packed.js."""
    ok = np.isfinite(field) & sea
    q = np.full(field.shape, 255, dtype=np.uint8)
    q[ok] = np.rint((np.clip(field[ok], lo, hi) - lo) / (hi - lo) * 254).astype(np.uint8)
    return {"range": [lo, hi], "data": base64.b64encode(q.tobytes()).decode("ascii")}


METHODS = {"new": "New model", "step05": "Current model (step 05)", "blend": "Blend rule"}
breakdown, areas, maps, checks = [], [], {}, []
persistence_rmse, persistence_new_rmse = {}, {}
for h in horizons:
    target = np.full(chl.shape, np.nan, dtype="float32")
    target[:-h] = chl[h:]
    valid = np.isfinite(target) & (target > 0) & mask[None] & in_test[:, None, None]
    t, i, j = np.nonzero(valid)
    X = pd.DataFrame({name: np.broadcast_to(inputs[name], chl.shape)[t, i, j] for name in config.MODEL_FEATURES}).astype("float32")
    observed = target[t, i, j].astype("float64")
    target_dates = dates[t] + pd.Timedelta(days=h)
    clim_log = F.climatology_for_dates(monthly_log_clim, dates + pd.Timedelta(days=h))[t, i, j].astype("float64")
    predicted = {
        "new": 10.0 ** bundle["models"][h].predict(X[bundle["feature_names"]]),
        "step05": 10.0 ** step05["models"][h].predict(X[step05["feature_names"]]),
        "blend": baselines.damped_persistence(bundle["damped_persistence_coefficients"][h],
                                              X["chl_latest"].to_numpy("float64"), clim_log),
    }
    # "No change", where there is a latest observation; not saved by the notebook, so not checked.
    latest = X["chl_latest"].to_numpy("float64")
    has_latest = np.isfinite(latest) & (latest > 0)
    persistence_rmse[h] = float(np.sqrt(np.mean((np.log10(latest[has_latest]) - np.log10(observed[has_latest])) ** 2)))
    persistence_new_rmse[h] = float(np.sqrt(np.mean((np.log10(predicted["new"][has_latest]) - np.log10(observed[has_latest])) ** 2)))
    log_obs = np.log10(observed)
    log_err = {k: np.log10(v) - log_obs for k, v in predicted.items()}
    for key, method in METHODS.items():
        rerun = float(np.sqrt(np.mean(log_err[key] ** 2)))
        saved = saved_score(method, h)
        checks.append((h, method, saved["RMSE (log10)"], rerun, saved["Scored pixel-days"], observed.size))

    def scores(sel):
        return {"n": int(sel.sum()),
                **{f"log_rmse_{k}": float(np.sqrt(np.mean(e[sel] ** 2))) for k, e in log_err.items()},
                **{f"bias_{k}": float(np.mean(predicted[k][sel] - observed[sel])) for k in predicted},
                **{f"median_rel_err_{k}": float(np.median(np.abs(predicted[k][sel] / observed[sel] - 1)) * 100) for k in predicted}}

    seasons = np.array([SEASONS[m] for m in target_dates.month])
    for name in ["Winter", "Spring", "Summer", "Autumn"]:
        breakdown.append({"horizon": h, "group": name, **scores(seasons == name)})
    breakdown.append({"horizon": h, "group": "High chlorophyll", **scores(log_obs - clim_log >= HIGH_ANOMALY_LOG10)})
    near = coast_km[i, j] <= COAST_KM
    areas.append({"horizon": h, "area": "coast", **scores(near)})
    areas.append({"horizon": h, "area": "offshore", **scores(~near)})

    # Per pixel: gain of the new model over the step 05 model, and over the blend.
    def per_pixel(e):
        total = np.zeros(mask.shape)
        np.add.at(total, (i, j), e ** 2)
        return total
    n = np.zeros(mask.shape, dtype=int)
    np.add.at(n, (i, j), 1)
    with np.errstate(all="ignore"):
        sums = {k: per_pixel(e) for k, e in log_err.items()}
        gain_step05 = 100 * (1 - np.sqrt(sums["new"] / sums["step05"]))
        gain_blend = 100 * (1 - np.sqrt(sums["new"] / sums["blend"]))
    few = (n < MIN_PAIRS) | ~mask
    gain_step05[few] = np.nan
    gain_blend[few] = np.nan
    ok = np.isfinite(gain_step05)
    maps[h] = {
        "gain_vs_step05": pack(gain_step05, -10.0, 10.0),
        "gain_vs_blend": pack(gain_blend, -30.0, 30.0),
        "summary": {
            "pixels": int(ok.sum()),
            "better_than_step05_pct": float(100 * np.mean(gain_step05[ok] > 0)),
            "better_than_blend_pct": float(100 * np.mean(gain_blend[ok] > 0)),
            "median_gain_vs_step05": float(np.median(gain_step05[ok])),
            "median_gain_coast_vs_step05": float(np.median(gain_step05[ok & (coast_km <= COAST_KM)])),
            "median_gain_offshore_vs_step05": float(np.median(gain_step05[ok & (coast_km > COAST_KM)])),
        },
    }
    print(f"+{h}d re-run done: {observed.size:,} pixel-days")

failed = [c for c in checks if abs(c[2] - c[3]) > 1e-6 or c[4] != c[5]]
for h, method, saved, rerun, n_saved, n_rerun in checks:
    print(f"  {'ok  ' if (h, method, saved, rerun, n_saved, n_rerun) not in failed else 'FAIL'} +{h}d {method:<24} "
          f"saved {saved:.6f} re-run {rerun:.6f}  ({n_rerun:,} pixel-days)")
if failed:
    sys.exit("The re-run does not reproduce the saved test scores: the data and the model are out of step.")
for row in areas:
    nb = next(r for r in area_notebook if r["horizon"] == row["horizon"]
              and (r["area"].startswith("Within") == (row["area"] == "coast")))
    if nb["n"] != row["n"] or abs(nb["new"] - row["log_rmse_new"]) > 5e-5:
        sys.exit(f"Coast/offshore re-run differs from the notebook: {nb} vs {row['n']}, {row['log_rmse_new']:.4f}")

OUT_PATH.write_text(json.dumps({
    "grid": {
        "latitude": [round(float(v), 5) for v in latitude],
        "longitude": [round(float(v), 5) for v in longitude],
        "sea": sea.astype(int).tolist(),
    },
    "pixels": int(mask.sum()),
    "removed_by_lower_bound": removed_by_lower_bound,
    "min_plausible_chl": config.MIN_PLAUSIBLE_CHL,
    "new_inputs": [{"name": n, "missing_pct": missing[n]} for n in config.EXTRA_FEATURES],
    "n_inputs": len(bundle["feature_names"]),
    "n_inputs_step05": len(step05["feature_names"]),
    "screening": [{"horizon": int(r["Horizon"][1:-1]), "candidate": r["Candidate"], "gain": r["Gain over blend (%)"],
                   "low": r["95% low"], "high": r["95% high"]} for r in bundle["screening"]],
    "tuning": tuning,
    "test_gains": [{"horizon": int(r["Horizon"][1:-1]), "vs": r["New model vs"], "gain": r["Gain (%)"],
                    "low": r["95% low"], "high": r["95% high"]} for r in bundle["test_gains"]],
    "test_scores": [{"horizon": int(r["Horizon"][1:-1]), "method": r["Method"], "log_rmse": r["RMSE (log10)"],
                     "bias": r["Bias (mg/m³)"], "median_rel_err": r["Median relative error (%)"],
                     "n": r["Scored pixel-days"]} for r in bundle["test_scores"]],
    "breakdown": breakdown,
    "areas": areas,
    "coast_km": COAST_KM,
    "maps": {str(h): m for h, m in maps.items()},
    "model_settings": {k: bundle["model_settings"][k] for k in ["learning_rate", "max_iter", "max_leaf_nodes", "min_samples_leaf"]},
    "promoted_utc": bundle["created_utc"],
    "high_anomaly_log10": HIGH_ANOMALY_LOG10,
    "vs_persistence": [{"horizon": h, "log_rmse_persistence": persistence_rmse[h], "log_rmse_new": persistence_new_rmse[h],
                        "gain": 100 * (1 - persistence_new_rmse[h] / persistence_rmse[h])} for h in horizons],
}, separators=(",", ":")))

print(f"Values removed by the lower bound: {removed_by_lower_bound}; missing %: { {k: round(v, 1) for k, v in missing.items()} }")
for r in breakdown + areas:
    label = r.get("group") or r["area"]
    print(f"+{r['horizon']}d {label:>16}: new {r['log_rmse_new']:.4f}  step05 {r['log_rmse_step05']:.4f}  blend {r['log_rmse_blend']:.4f}"
          f"  vs05 {100 * (1 - r['log_rmse_new'] / r['log_rmse_step05']):+5.1f}%  vsblend {100 * (1 - r['log_rmse_new'] / r['log_rmse_blend']):+5.1f}%"
          f"  bias new {r['bias_new']:+.4f}  n={r['n']:,}")
for h in horizons:
    print(f"+{h}d vs no change: {100 * (1 - persistence_new_rmse[h] / persistence_rmse[h]):.1f}% (rows with a latest observation)")
for h, m in maps.items():
    print(f"+{h}d maps: {m['summary']}")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
