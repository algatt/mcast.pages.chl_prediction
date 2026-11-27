"""Build the data behind the Step 07 page (07-NRT-Input-Validation.ipynb).

Reads the most recent live (near-real-time) forecast the notebook saved, with
its bloom probabilities, the most recent live evaluation (scores of past live
forecasts, chlorophyll and blooms), and the local NRT archive written by
08-NRT-Archive.ipynb, and saves website/src/data/nb07.json.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb07_data.py
"""

import base64
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiment_v2"
FORECASTS = EXP / "data/processed/nrt_forecasts"
EVALUATIONS = EXP / "data/processed/nrt_evaluation"
ARCHIVE = EXP / "data/raw/nrt_archive"
L4 = (
    EXP
    / "data/chl_l3_l4_comparison/chl_L4_2022-01-01_2025-12-31_13.9_15.2_35.55_36.9.nc"
)
OUT_PATH = ROOT / "website/src/data/nb07.json"

with xr.open_dataset(L4) as ds:
    sea = np.isfinite(ds["CHL"].sortby("latitude").sortby("longitude").values).any(
        axis=0
    )


def pack(field, lo, hi):
    """One byte per pixel over [lo, hi], 255 = no value; see src/data/packed.js."""
    ok = np.isfinite(field) & sea
    q = np.full(field.shape, 255, dtype=np.uint8)
    q[ok] = np.rint((np.clip(field[ok], lo, hi) - lo) / (hi - lo) * 254).astype(
        np.uint8
    )
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
    "generated_utc": forecast.attrs.get("generated_utc", ""),
    "published_methods": json.loads(
        forecast.attrs.get("published_method_by_horizon_json", "{}")
    ),
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
        **{
            f"forecast_{int(h)}": pack(
                log_or_nan(
                    np.where(
                        mask, forecast["chl_forecast"].sel(horizon=h).values, np.nan
                    )
                ),
                -2.0,
                1.0,
            )
            for h in forecast.horizon.values
        },
        "latest": pack(
            log_or_nan(np.where(mask, inputs["chl_latest"].values, np.nan)), -2.0, 1.0
        ),
        "age": pack(np.where(mask, age, np.nan), 0.0, 14.0),
        "sst": pack(np.where(mask, inputs["sst_c"].values, np.nan), 15.0, 30.0),
        "fallback": pack(
            np.where(mask & ~history, 1.0, np.where(mask, 0.0, np.nan)), 0.0, 1.0
        ),
    },
}
# When the newest chlorophyll was first downloaded, to compare with the 20:00 UTC schedule.
with xr.open_dataset(ARCHIVE / "chl" / f"{live['latest_chl_date']}.nc") as ds:
    live["chl_retrieved_utc"] = ds.attrs.get("retrieved_utc", "")

# Today's bloom probabilities (step 10's model, run by step 07).
blooms_path = latest / "bloom_probabilities.nc"
if not blooms_path.exists():
    # A map-only rerun may follow a full run for exactly the same issue and inputs.
    for candidate in sorted(FORECASTS.glob("*/bloom_probabilities.nc"), reverse=True):
        with xr.open_dataset(candidate.parent / "nrt_features.nc") as prior:
            if inputs.equals(prior):
                blooms_path = candidate
                break
if blooms_path.exists():
    with xr.open_dataset(blooms_path) as b:
        live["blooms"] = {
            "model_file": b.attrs.get("bloom_model_file", ""),
            "thresholds": {
                str(int(h)): float(b["warning_threshold"].sel(horizon=h))
                for h in b.horizon.values
            },
            "area_warned_pct": {
                str(int(h)): float(
                    100 * b["bloom_warning"].sel(horizon=h).values[mask].mean()
                )
                for h in b.horizon.values
            },
            "highest_pct": {
                str(int(h)): float(
                    100 * np.nanmax(b["bloom_probability"].sel(horizon=h).values[mask])
                )
                for h in b.horizon.values
            },
        }
        live["maps"].update(
            {
                f"bloom_{int(h)}": pack(
                    np.where(
                        mask, b["bloom_probability"].sel(horizon=h).values, np.nan
                    ),
                    0.0,
                    1.0,
                )
                for h in b.horizon.values
            }
        )
sst_values = inputs["sst_c"].values[mask & np.isfinite(inputs["sst_c"].values)]
# None when the forecast was issued before the issue day's temperature was archived.
live["sst_range"] = (
    [float(sst_values.min()), float(sst_values.max())] if sst_values.size else None
)

# --- The local NRT archive ----------------------------------------------------------
archive = {}
for source in ["chl", "chl_l4", "sst"]:
    dates = sorted(p.stem for p in (ARCHIVE / source).glob("*.nc"))
    expected = pd.date_range(dates[0], dates[-1], freq="D").strftime("%Y-%m-%d")
    archive[source] = {
        "days": len(dates),
        "first": dates[0],
        "last": dates[-1],
        "missing": sorted(set(expected) - set(dates)),
    }


# --- Scores of past live forecasts (the most recent run of step 07) ------------------
run_dir = sorted(p for p in EVALUATIONS.iterdir() if (p / "scores.json").exists())[-1]
provenance = json.loads((run_dir / "provenance.json").read_text())
clean = lambda v: (
    None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v
)
evaluation = {
    "run": run_dir.name,
    "saved_utc": provenance["saved_utc"],
    "first_issue_day": provenance["first_complete_issue_day"],
    "last_target_day": provenance["chl_archive_days"][1],
    "model_file": provenance["model_file"],
    "scores": [
        {
            "horizon": r["Horizon"],
            "method": r["Method"],
            "issue_days": r["Scored issue days"],
            "pixel_days": r["Scored pixel-days"],
            "log_rmse": r["RMSE (log10)"],
            "median_error_pct": r["Median relative error (%)"],
        }
        for r in json.loads((run_dir / "scores.json").read_text())
    ],
    "gains": [
        {
            "horizon": r["Horizon"],
            "issue_days": r["Issue days"],
            "gain": clean(r["Gain over blend (%)"]),
            "low": clean(r["95% low"]),
            "high": clean(r["95% high"]),
        }
        for r in json.loads((run_dir / "gain_intervals.json").read_text())
    ],
}
# Scores split by product version (inputs → targets), when step 07 saved them.
if (run_dir / "scores_by_version.json").exists():
    evaluation["by_version"] = [
        {
            "horizon": r["Horizon"],
            "versions": r["Inputs → targets"],
            "same_version": r["Same version"],
            "issue_days": r["Issue days"],
            "pixel_days": r["Pixel-days"],
            "first_issue_day": r["First issue day"],
            "last_issue_day": r["Last issue day"],
            "model_bias_log": r["Bias log10: Forecast model"],
            "blend_bias_log": r["Bias log10: Blend rule"],
            "gain": clean(r["Gain over blend (%)"]),
            "low": clean(r["95% low"]),
            "high": clean(r["95% high"]),
        }
        for r in json.loads(
            (run_dir / "scores_by_version.json").read_text(encoding="utf-8")
        )
    ]
# For comparison: the same gain on the 2025 test year, saved with the model in use (step 09).
model_bundle = joblib.load(EXP / "models" / provenance["model_file"])
evaluation["test_gains"] = [
    {
        "horizon": r["Horizon"],
        "gain": r["Gain (%)"],
        "low": r["95% low"],
        "high": r["95% high"],
    }
    for r in model_bundle["test_gains"]
    if r["New model vs"] == "Blend rule"
]
evaluation["test_year"] = int(model_bundle["test_year"])
# The hedge test (step 12): forecasts issued from its start date only.
if (run_dir / "hedge_test.json").exists():
    test = json.loads((run_dir / "hedge_test.json").read_text())
    evaluation["hedge_test"] = {
        "test_from": test["test_from"],
        "decision_days": test["decision_days"],
        "model_weight": test["model_weight"],
        "decision": test["decision"],
        "scores": [
            {
                "horizon": r["Horizon"],
                "method": r["Method"],
                "issue_days": r["Issue days"],
                "log_rmse": clean(r.get("RMSE (log10)")),
            }
            for r in test["scores"]
        ],
        "gains": [
            {
                "horizon": r["Horizon"],
                "comparison": r["Comparison"],
                "issue_days": r["Issue days"],
                "gain": clean(r["Gain (%)"]),
                "low": clean(r["95% low"]),
                "high": clean(r["95% high"]),
            }
            for r in test["gains"]
        ],
    }
if (run_dir / "bloom_scores.json").exists():
    evaluation["blooms"] = [
        {
            "horizon": r["Horizon"],
            "method": r["Method"],
            "issue_days": r["Issue days"],
            "pixel_days": r["Pixel-days"],
            "bloom_pct": r["Bloom share (%)"],
            "mean_probability_pct": r["Mean probability (%)"],
            "skill_vs_usual": clean(r["Skill vs usual frequency (%)"]),
            "low_vs_usual": clean(r["vs usual frequency: 95% low"]),
            "high_vs_usual": clean(r["vs usual frequency: 95% high"]),
            "warnings": clean(r.get("Warnings")),
            "hit_rate_pct": clean(r.get("Hit rate (%)")),
            "false_alarm_pct": clean(r.get("False alarm ratio (%)")),
        }
        for r in json.loads((run_dir / "bloom_scores.json").read_text())
    ]

OUT_PATH.write_text(
    json.dumps(
        {
            "grid": {
                "latitude": [round(float(v), 5) for v in forecast.latitude.values],
                "longitude": [round(float(v), 5) for v in forecast.longitude.values],
                "sea": sea.astype(int).tolist(),
            },
            "live": live,
            "archive": archive,
            "evaluation": evaluation,
        },
        separators=(",", ":"),
    )
)

print(json.dumps({k: v for k, v in live.items() if k != "maps"}, indent=1))
print(json.dumps(archive, indent=1))
print(
    f"Live evaluation {evaluation['run']}: issue days from {evaluation['first_issue_day']}, "
    f"targets to {evaluation['last_target_day']}; gains over blend "
    + ", ".join(
        f"{g['horizon']} {g['gain']:+.1f}%"
        for g in evaluation["gains"]
        if g["gain"] is not None
    )
)
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
