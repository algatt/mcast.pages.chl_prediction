"""Build the data behind the Step 12 page (12-Wind-Event-Check.ipynb).

Reads the most recent results of the notebook from
experiment_v2/data/processed/wind_check/: how often sudden changes follow windy and
calm days, whether wind says which way chlorophyll moves, the model's gain over the
blend rule by wind class, and the hedge. Saves website/src/data/nb12.json.

A few numbers the notebook printed but did not save (the number of issue days, the
sudden-change thresholds, the correlation of wind with the signed change) are
recomputed here from issue_days.csv with the notebook's own rules. The script stops
if that recomputation does not reproduce the saved results.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb12_data.py
"""

from pathlib import Path
import json
import math

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiment_v2/data/processed/wind_check"
OUT_PATH = ROOT / "website/src/data/nb12.json"

# The notebook's rules (cell 1 of 12-Wind-Event-Check.ipynb).
SUDDEN_TOP_SHARE = 0.10
MIN_PIXELS = 500
N_CLASSES = 5
PRIMARY = "Strongest of past 3 days"
SEASONS = ["Winter", "Spring", "Summer", "Autumn"]

runs = sorted(p for p in RESULTS.iterdir() if p.is_dir() and (p / "wind_vs_change.json").exists())
if not runs:
    raise SystemExit(f"No results found in {RESULTS}")
run = runs[-1]


def read(name):
    return json.loads((run / f"{name}.json").read_text())


def clean(v):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return None
    return round(v, 4) if isinstance(v, float) else v


prov = read("provenance")
wind_vs_change = read("wind_vs_change")
by_class = read("sudden_by_wind_class")
direction = read("direction_by_wind_class")
by_season = read("sudden_by_season_and_class")
error_by_group = read("model_error_by_group")
hedge = read("hedge")

# --- Recompute what the notebook printed but did not save --------------------------------
days = pd.read_csv(run / "issue_days.csv", parse_dates=["Issue day"])
d1 = days[(days["Horizon"] == 1) & (days["Pixels"] >= MIN_PIXELS)].copy()
d1["Sudden"] = d1.groupby("Season")["Mean abs change"].transform(lambda s: s >= s.quantile(1 - SUDDEN_TOP_SHARE))

primary = d1.dropna(subset=[PRIMARY]).copy()
primary["Wind class"] = primary.groupby("Season")[PRIMARY].transform(
    lambda s: pd.qcut(s.rank(method="first"), N_CLASSES, labels=False) + 1)
wind_rank = primary.groupby("Season")[PRIMARY].rank(pct=True)
size_rank = primary.groupby("Season")["Mean abs change"].rank(pct=True)
rho_size = wind_rank.corr(size_rank, method="spearman")
rho_signed = wind_rank.corr(primary["Mean change"], method="spearman")

saved_primary = next(r for r in wind_vs_change if r["Wind measure"] == PRIMARY)
checks = {
    "issue days with the primary wind measure": (len(primary), saved_primary["Issue days"]),
    "issue days per wind class": (primary["Wind class"].value_counts().sort_index().tolist(),
                                  [r["Issue days"] for r in by_class]),
    "correlation of wind with the size of the change": (round(rho_size, 6),
                                                         round(saved_primary["Correlation with next-day change"], 6)),
}
for name, (mine, saved) in checks.items():
    if mine != saved:
        raise SystemExit(f"Recomputation does not match the notebook ({name}): {mine} against {saved}. "
                         "Has the notebook's method changed?")

thresholds = {s: round(float(100 * (10 ** d1.loc[d1["Sudden"] & (d1["Season"] == s), "Mean abs change"].min() - 1)), 1)
              for s in SEASONS}

# --- Tidy the saved tables ----------------------------------------------------------------
measures = [{
    "measure": r["Wind measure"], "issue_days": r["Issue days"],
    "correlation": clean(r["Correlation with next-day change"]),
    "correlation_low": clean(r["95% low"]), "correlation_high": clean(r["95% high"]),
    "sudden_windiest_pct": clean(r["Sudden days, windiest fifth (%)"]),
    "sudden_calmest_pct": clean(r["Sudden days, calmest fifth (%)"]),
    "ratio": clean(r["Ratio"]), "ratio_low": clean(r["Ratio 95% low"]), "ratio_high": clean(r["Ratio 95% high"]),
} for r in wind_vs_change]

classes = [{
    "wind_class": r["Wind class"], "issue_days": r["Issue days"],
    "sudden_pct": clean(r["Sudden days (%)"]), "mean_change_pct": clean(r["Mean next-day change (%)"]),
    "wind_median_ms": clean(r["Wind (m/s), median"]),
    "rising_pct": clean(d["Days rising (%)"]), "sudden_rising_pct": clean(d["Sudden days rising (%)"]),
    "average_change_pct": clean(d["Average change (%)"]),
} for r, d in zip(by_class, direction)]

seasons = [{"season": r["Season"], "sudden_pct": {k: clean(r[str(k)]) for k in range(1, N_CLASSES + 1)}}
           for r in sorted(by_season, key=lambda r: SEASONS.index(r["Season"]))]

groups = [{
    "years": r["Years"], "group": r["Group"], "issue_days": r["Issue days"],
    "model_gain": clean(r["Gain over blend (%)"]), "hedge_gain": clean(r["Hedge gain over blend (%)"]),
    "share": clean(r["Share of the overall difference (%)"]),
} for r in error_by_group]

hedge_rows = [{
    "data": r["Data"], "horizon": int(r["Horizon"].strip("+d")),
    "model_gain": clean(r["Model vs blend (%)"]), "hedge_gain": clean(r["Hedge vs blend (%)"]),
} for r in hedge]

out = {
    "run": run.name,
    "saved_utc": prov["saved_utc"],
    "model_file": prov["model_file"],
    "trained_until": prov["model_training_issue_dates"][1],
    "years": [prov["years"][0], prov["years"][-1]],
    "decision": prov["decision"],
    "decision_rule": {"measure": PRIMARY, "ratio": 1.5},
    "hedge_weight_model": prov["hedge_weight_model"],
    "live_chl_archive_days": prov["live_chl_archive_days"],
    "issue_days": len(d1),
    "sudden_days": int(d1["Sudden"].sum()),
    "sudden_threshold_pct": thresholds,
    "correlation_size": round(rho_size, 4),
    "correlation_signed": round(rho_signed, 4),
    "measures": measures,
    "classes": classes,
    "seasons": seasons,
    "groups": groups,
    "hedge": hedge_rows,
}
OUT_PATH.write_text(json.dumps(out, indent=1))

print(f"Run {run.name}, model {prov['model_file']}, years {prov['years'][0]}–{prov['years'][-1]}")
print(f"+1 day: {len(d1):,} issue days, {out['sudden_days']} sudden-change days; thresholds by season: {thresholds}")
print(f"{PRIMARY}: ratio {saved_primary['Ratio']:.2f} ({saved_primary['Ratio 95% low']:.2f}–{saved_primary['Ratio 95% high']:.2f}); "
      f"decision: {prov['decision']}")
print(f"Wind against the size of the change {rho_size:+.2f}, against its direction {rho_signed:+.2f}")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
