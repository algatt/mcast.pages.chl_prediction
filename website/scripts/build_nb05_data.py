"""Build the data behind the Step 05 page (05-Baselines-and-Modelling.ipynb).

Sources, in order of preference:
  * the saved model bundle (validation and test results, bootstrap intervals,
    baseline coefficients, model settings);
  * the training-years experiment table recorded in the notebook's last cell;
  * a re-run of the saved model on the 2025 test rows, for breakdowns by season
    and month. The re-run is checked against the saved test scores first.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb05_data.py
"""

from pathlib import Path
import json
import re

import joblib
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
BUNDLE = EXP / "models/chl_forecast_1_4_7d.joblib"
PREPARED = EXP / "data/processed/malta_forecast_prepared.nc"
NOTEBOOK = EXP / "05-Baselines-and-Modelling.ipynb"
OUT_PATH = ROOT / "website/src/data/nb05.json"

HIGH_ANOMALY_LOG10 = 0.2          # as in the notebook: at least 1.6 × the monthly normal
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}

bundle = joblib.load(BUNDLE)
features = bundle["feature_names"]
horizons = bundle["forecast_horizons_days"]


def table(frame, index_names):
    out = []
    for idx, row in frame.iterrows():
        idx = idx if isinstance(idx, tuple) else (idx,)
        out.append({**dict(zip(index_names, idx)),
                    **{k: (None if pd.isna(v) else float(v)) for k, v in row.items() if k != "Clearly better"},
                    **({"clearly_better": bool(row["Clearly better"])} if "Clearly better" in row else {})})
    return out


validation = table(bundle["validation_results"], ["horizon", "method"])
test = table(bundle["test_results"], ["horizon", "method"])
intervals = table(bundle["test_gain_intervals"], ["horizon", "baseline"])

# --- Training-years experiment, from the notebook's recorded markdown table ------
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
markdown = "".join(nb["cells"][-1]["source"])
era = []
for line in markdown.splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 5 and re.fullmatch(r"\d{4}–\d{4}", cells[1]):
        era.append({"method": cells[0], "years": cells[1],
                    "log_rmse": {h: float(v) for h, v in zip(horizons, cells[2:])}})
assert len(era) == 8, "training-years table not found in the notebook"

# --- Re-run the saved model on the 2025 test rows --------------------------------
data = xr.open_dataset(PREPARED)
mask = data["model_mask"].values == 1
in_test = data["split_test"].values == 1
days = np.flatnonzero(in_test)
block = slice(days[0], days[-1] + 1)
subset = data.isel(time=block)
issue_dates = pd.DatetimeIndex(subset.time.values)


def grid(name, ds=subset):
    return ds[name].transpose("time", "latitude", "longitude").values


breakdown = {"season": [], "month": []}
checks = []
for h in horizons:
    target = grid(f"chl_target_{h}d")
    valid = np.isfinite(target) & (target > 0) & mask[None] & in_test[block][:, None, None]
    t, i, j = np.nonzero(valid)
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
    observed = target[t, i, j].astype("float64")
    persistence = X["chl_latest"].to_numpy("float64")
    clim_log = grid("chl_clim_log", data["chl_clim_log"].shift(time=-h).isel(time=block).to_dataset())[t, i, j]
    a, b, c = bundle["damped_persistence_coefficients"][h]
    damped = 10 ** (a + b * np.log10(persistence) + c * clim_log)
    model = 10 ** bundle["models"][h].predict(X[features])

    log_obs = np.log10(observed)
    sq = {"model": (np.log10(model) - log_obs) ** 2,
          "damped": (np.log10(damped) - log_obs) ** 2,
          "persistence": (np.log10(persistence) - log_obs) ** 2}
    err = {"model": model - observed, "damped": damped - observed, "persistence": persistence - observed}

    # Check: the re-run reproduces the saved log RMSE of the forecast model.
    saved = bundle["test_results"].loc[(f"+{h}d", "Forecast model"), "RMSE (log10)"]
    rerun = float(np.sqrt(sq["model"].mean()))
    checks.append((h, saved, rerun))
    assert abs(saved - rerun) < 1e-9, (h, saved, rerun)

    target_dates = issue_dates[t] + pd.Timedelta(days=h)
    seasons = np.array([SEASONS[m] for m in target_dates.month])
    high = log_obs - clim_log >= HIGH_ANOMALY_LOG10

    def scores(sel):
        return {
            "n": int(sel.sum()),
            **{f"log_rmse_{k}": float(np.sqrt(v[sel].mean())) for k, v in sq.items()},
            **{f"bias_{k}": float(v[sel].mean()) for k, v in err.items()},
            **{f"median_rel_err_{k}": float(np.median(np.abs(v[sel]) / observed[sel]) * 100) for k, v in err.items()},
        }

    for name in ["Winter", "Spring", "Summer", "Autumn"]:
        breakdown["season"].append({"horizon": h, "group": name, **scores(seasons == name)})
    breakdown["season"].append({"horizon": h, "group": "High chlorophyll", **scores(high)})
    for m in range(1, 13):
        sel = target_dates.month == m
        breakdown["month"].append({"horizon": h, "month": m, **scores(sel)})

params = bundle["models"][1].get_params()
OUT_PATH.write_text(json.dumps({
    "features": features,
    "feature_set": bundle["feature_set"],
    "training_issue_dates": bundle["training_issue_date_range"],
    "train_sample_fraction": bundle["train_sample_fraction"],
    "climatology_period": bundle["climatology_period"],
    "damped_coefficients": {str(h): v for h, v in bundle["damped_persistence_coefficients"].items()},
    "model_settings": {k: params[k] for k in ["learning_rate", "max_iter", "max_leaf_nodes", "min_samples_leaf", "l2_regularization"]},
    "validation": validation,
    "test": test,
    "intervals": intervals,
    "era": era,
    "breakdown": breakdown,
    "high_anomaly_log10": HIGH_ANOMALY_LOG10,
}, separators=(",", ":")))

for h, saved, rerun in checks:
    print(f"+{h}d model log RMSE: saved {saved:.6f}, re-run {rerun:.6f}")
for r in breakdown["season"]:
    print(f"+{r['horizon']}d {r['group']:>16}: model {r['log_rmse_model']:.4f}  damped {r['log_rmse_damped']:.4f}  "
          f"gain {100 * (1 - r['log_rmse_model'] / r['log_rmse_damped']):5.1f}%  bias model {r['bias_model']:+.4f}  n={r['n']:,}")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
