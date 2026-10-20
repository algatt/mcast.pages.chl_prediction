"""Build the data behind the Step 08 page (08-NRT-Archive.ipynb).

Reads the local near-real-time archive the notebook writes and saves
website/src/data/nb08.json: which days are held for each source, how many
pixels each chlorophyll day observed, the archive runs so far, and the
earliest date a full live check (step 07) becomes possible.

Run from the repository root with the experiment environment:

    experiment_v2/.venv/bin/python website/scripts/build_nb08_data.py
"""

from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "experiment_v2/data/raw/nrt_archive"
OUT_PATH = ROOT / "website/src/data/nb08.json"

HISTORY_DAYS = 7        # inputs: seven days of chlorophyll history
CHL_LAG_DAYS = 1        # yesterday's chlorophyll is the newest available
LONGEST_HORIZON = 7

log = pd.read_csv(ARCHIVE / "archive_log.csv")
saved = log[log["Status"] == "Saved"]

sources = {}
for source in ["chl", "chl_l4", "sst"]:
    files = sorted((ARCHIVE / source).glob("*.nc"))
    dates = [p.stem for p in files]
    expected = pd.date_range(dates[0], dates[-1], freq="D").strftime("%Y-%m-%d")
    pixels = saved[saved["Source"] == source].set_index("Date")["Valid pixels"].to_dict()
    sources[source] = {
        "first": dates[0],
        "last": dates[-1],
        "days": len(dates),
        "missing": sorted(set(expected) - set(dates)),
        "size_kb": round(sum(p.stat().st_size for p in files) / 1024),
        "valid_pixels": {d: int(pixels[d]) for d in dates if d in pixels},
    }

runs = [{"retrieved_utc": t, "saved": int((saved["Retrieved (UTC)"] == t).sum())}
        for t in sorted(log["Retrieved (UTC)"].unique())]

# A full check of a +7-day forecast needs 7 days of history before the issue
# day, and the target observation, which is published the day after it.
first = pd.Timestamp(sources["chl"]["first"])
first_issue = first + pd.Timedelta(days=HISTORY_DAYS + CHL_LAG_DAYS - 1)
first_target = first_issue + pd.Timedelta(days=LONGEST_HORIZON)
first_check = first_target + pd.Timedelta(days=CHL_LAG_DAYS)

OUT_PATH.write_text(json.dumps({
    "sources": sources,
    "runs": runs,
    "first_full_check": {
        "issue_date": str(first_issue.date()),
        "target_date": str(first_target.date()),
        "available_from": str(first_check.date()),
    },
}, indent=1))

print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "valid_pixels"} for k, v in sources.items()}, indent=1))
print("runs:", runs)
print("first full check:", first_issue.date(), "→", first_target.date(), "available", first_check.date())
print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
