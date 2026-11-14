"""Build the data behind the Step 11 page (11-MY-vs-NRT.ipynb and 11-MY-vs-NRT_part_b.ipynb).

Reads the most recent results of both notebooks from
experiment_v2/data/processed/my_vs_nrt/: Part A (the live window on the archive in
every year, input shifts, the temperature test) and Part B (the live feed against
the archive on the same days, the inputs/targets test, the live errors by day),
and saves website/src/data/nb11.json.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb11_data.py
"""

from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiment_v2/data/processed/my_vs_nrt"
OUT_PATH = ROOT / "website/src/data/nb11.json"


def latest(pattern_ok):
    runs = sorted(p for p in RESULTS.iterdir() if p.is_dir() and pattern_ok(p))
    if not runs:
        raise SystemExit(f"No results found in {RESULTS}")
    return runs[-1]


def read(folder, name):
    return json.loads((folder / f"{name}.json").read_text())


def clean(v):
    return None if v is None or (isinstance(v, float) and not math.isfinite(v)) else v


def horizon(h):
    return int(h.strip("+d"))


part_a = latest(lambda p: (p / "window_comparison.json").exists())
part_b = latest(lambda p: (p / "inputs_targets_test.json").exists())
prov_a, prov_b = read(part_a, "provenance"), read(part_b, "provenance")


def gain_row(r):
    return {"horizon": horizon(r["Horizon"]), "issue_days": r["Issue days"],
            "pixels_per_day": round(r["Pixel-days per issue day"] if "Pixel-days per issue day" in r
                                    else r["Pixel-days"] / r["Issue days"]),
            "rmse_model": r["RMSE log10: Forecast model"], "rmse_blend": r["RMSE log10: Blend rule"],
            "rmse_no_change": r["RMSE log10: No change"],
            "gain": clean(r["Gain over blend (%)"]), "low": clean(r["95% low"]), "high": clean(r["95% high"]),
            # The estimate alone, also where there are too few issue days for a 95% range.
            "gain_point": 100 * (1 - r["RMSE log10: Forecast model"] / r["RMSE log10: Blend rule"])}


# --- Part A ------------------------------------------------------------------------
window = [{"data": r["Data"], **gain_row(r)} for r in read(part_a, "window_comparison")]
by_year = [{"year": r["Year"], **gain_row(r)} for r in read(part_a, "window_by_year")]
temperature = [{"data": r["Data"], **gain_row(r)} for r in read(part_a, "temperature_ablation")]
shifts = [{"input": r["Input"], "live_mean": r["Live NRT mean"], "my_mean": r["MY mean"],
           "my_yearly": r["MY yearly means"], "shift_sd": r["Shift (MY s.d.)"],
           "live_missing_pct": r["Live missing (%)"], "my_missing_pct": r["MY missing (%)"]}
          for r in read(part_a, "input_shifts")]

# --- Part B ------------------------------------------------------------------------
coverage = [{"date": r["Date"][:10], "nrt": r["NRT pixels"], "my": r["MY pixels"], "both": r["Both"],
             "nrt_only": r["NRT only"], "my_only": r["MY only"]}
            for r in read(part_b, "overlap_coverage")]
values = read(part_b, "overlap_values")
overall = next(r for r in values if r["Days"] == "All overlap")
value_days = [{"date": r["Days"], "pixel_days": r["Pixel-days"], "bias": r["Bias (log10)"], "rmsd": r["RMSD (log10)"],
               "correlation": r["Correlation"], "within_pct": r["Share within ±0.05 log10 (%)"]}
              for r in values if r["Days"] != "All overlap"]
decisive = [{"inputs": r["Inputs"], "targets": r["Targets"], **gain_row(r)} for r in read(part_b, "inputs_targets_test")]
pipeline = [{"data": r["Data"], **gain_row(r)} for r in read(part_b, "pipeline_check")]
by_day_file = sorted(part_b.glob("live_by_issue_day_*d.json"))[-1]
by_day = [{"date": r["Issue day"], "pixel_days": r["Pixel-days"], "change": r["Observed change (log10)"],
           "rmse_model": r["RMSE: model"], "rmse_blend": r["RMSE: blend"],
           "bias_model": r["Bias: model"], "bias_blend": r["Bias: blend"],
           "better": r["Better"], "excess_share": r["Excess error share (%)"]}
          for r in json.loads(by_day_file.read_text())]

OUT_PATH.write_text(json.dumps({
    "part_a_run": part_a.name,
    "part_b_run": part_b.name,
    "model_file": prov_a["model_file"],
    "trained_until": prov_a["model_training_issue_dates"][1],
    "window": prov_a["window_first_issue_to_last_target"],
    "years_in_training": prov_a["my_years_in_training"],
    "years_unseen": prov_a["my_years_unseen"],
    "live_chl_days": prov_b["live_chl_archive_days"],
    "first_issue_day": prov_b["first_complete_issue_day"],
    "overlap_days": prov_b["overlap_days"],
    "my_dataset_id": prov_b["my_dataset_id"],
    "my_retrieved_utc": prov_b["my_retrieved_utc"],
    "by_day_horizon": int(by_day_file.stem.split("_")[-1].rstrip("d")),
    "window_comparison": window,
    "by_year": by_year,
    "temperature_test": temperature,
    "input_shifts": shifts,
    "coverage": coverage,
    "values": {"pixel_days": overall["Pixel-days"], "bias": overall["Bias (log10)"], "sd": overall["S.d. (log10)"],
               "rmsd": overall["RMSD (log10)"], "correlation": overall["Correlation"],
               "median_ratio": overall["NRT/MY median ratio"], "within_pct": overall["Share within ±0.05 log10 (%)"],
               "days": value_days},
    "inputs_targets_test": decisive,
    "pipeline_check": pipeline,
    "by_day": by_day,
}, indent=1, ensure_ascii=False))

print(f"Part A: {part_a.name}; Part B: {part_b.name}; window {prov_a['window_first_issue_to_last_target']}")
print(f"Overlap {prov_b['overlap_days']}: RMSD {overall['RMSD (log10)']:.4f} log10, correlation {overall['Correlation']:.3f}")
for r in decisive:
    print(f"  +{r['horizon']}d inputs {r['inputs']}, targets {r['targets']}: gain over blend {r['gain']:+.1f}%")
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
