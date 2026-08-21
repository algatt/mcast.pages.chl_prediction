"""Export the notebook-style actual/predicted/residual viewer for the website.

The frames use the final v2 single-split models and the exact sampled 2023 test
rows. Available scattered rows are linearly interpolated onto the CHL grid only
for display, matching Notebook 07's viewer. No interpolated values enter model
training or evaluation.

Run from the repository root:
    .venv/Scripts/python.exe experiment/export_prediction_frames.py
"""

from pathlib import Path
import json
import shutil
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.interpolate import griddata
import xarray as xr
import xgboost as xgb


HORIZONS = list(range(1, 8))
N_DATES = 48
DPI = 92
CHL_VMIN, CHL_VMAX = -2.0, 0.5
RES_LIM = 0.5

HERE = Path(__file__).resolve().parent
PROC_DIR = HERE / "data" / "processed"
MODEL_DIR = HERE / "models"
OUT_DIR = HERE.parent / "website" / "public" / "figs" / "pred_frames"

SAMPLE_PATH = PROC_DIR / "supervised_sample_v2.parquet"
FEATURE_MANIFEST_PATH = PROC_DIR / "feature_manifest_v2.json"
SPLIT_MANIFEST_PATH = PROC_DIR / "split_manifest.json"
CHL_GRID_PATH = HERE / "data" / "raw" / "chl_malta_2021_2023.nc"

for path in (SAMPLE_PATH, FEATURE_MANIFEST_PATH, SPLIT_MANIFEST_PATH, CHL_GRID_PATH):
    if not path.exists():
        raise FileNotFoundError(path)

started = time.time()
df = pd.read_parquet(SAMPLE_PATH)
df["time"] = pd.to_datetime(df["time"])

feature_manifest = json.loads(FEATURE_MANIFEST_PATH.read_text())
split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text())
feature_cols = feature_manifest["feature_cols"]

if feature_manifest["horizons"] != HORIZONS:
    raise RuntimeError("Unexpected horizon set in feature_manifest_v2.json")

test_start = pd.Timestamp(split_manifest["test_start"])
test_end = pd.Timestamp(split_manifest["test_end"])
test = (
    df[df["time"].between(test_start, test_end)]
    .sort_values(["time", "latitude", "longitude"])
    .reset_index(drop=True)
)

models = {}
diagnostics = {}
for horizon in HORIZONS:
    model_path = MODEL_DIR / f"xgb_v2_h{horizon}.json"
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    model = xgb.XGBRegressor()
    model.load_model(model_path)
    model_features = model.get_booster().feature_names
    if model_features is not None and list(model_features) != list(feature_cols):
        raise RuntimeError(f"H+{horizon} model feature order does not match v2 manifest")

    target = f"target_h{horizon}"
    mask = test[target].notna()
    frame = test.loc[mask, ["time", "latitude", "longitude"]].copy()
    frame["actual"] = test.loc[mask, target].to_numpy()
    frame["predicted"] = model.predict(test.loc[mask, feature_cols])
    frame["residual"] = frame["predicted"] - frame["actual"]

    models[horizon] = model
    diagnostics[horizon] = frame
    print(f"H+{horizon}: predicted {len(frame):,} observed-target rows")

common_dates = sorted(
    set.intersection(*(set(frame["time"].unique()) for frame in diagnostics.values()))
)
if len(common_dates) < N_DATES:
    raise RuntimeError(f"Only {len(common_dates)} common test dates are available")

selected_indices = np.linspace(0, len(common_dates) - 1, N_DATES, dtype=int)
selected_dates = [pd.Timestamp(common_dates[i]) for i in selected_indices]

chl_grid = xr.open_dataset(CHL_GRID_PATH)["CHL"]
grid_lon = chl_grid.longitude.values
grid_lat = chl_grid.latitude.values
lon_mesh, lat_mesh = np.meshgrid(grid_lon, grid_lat)


def interpolate(day, column):
    points = day[["longitude", "latitude"]].to_numpy()
    if len(points) < 4:
        return np.full(lon_mesh.shape, np.nan)
    return griddata(points, day[column].to_numpy(), (lon_mesh, lat_mesh), method="linear")


if OUT_DIR.exists():
    resolved = OUT_DIR.resolve()
    expected_parent = (HERE.parent / "website" / "public" / "figs").resolve()
    if resolved.parent != expected_parent:
        raise RuntimeError(f"Refusing to replace unexpected output directory: {resolved}")
    shutil.rmtree(resolved)
OUT_DIR.mkdir(parents=True)

mae_by_horizon = {}
rows_by_horizon = {}

for horizon in HORIZONS:
    horizon_dir = OUT_DIR / f"h{horizon}"
    horizon_dir.mkdir()
    maes = []
    row_counts = []

    for frame_index, issue_date in enumerate(selected_dates):
        day = diagnostics[horizon][diagnostics[horizon]["time"] == issue_date]
        if day.empty:
            raise RuntimeError(f"No H+{horizon} rows on {issue_date.date()}")

        actual_grid = interpolate(day, "actual")
        predicted_grid = interpolate(day, "predicted")
        residual_grid = interpolate(day, "residual")
        sampled_mae = float(np.mean(np.abs(day["residual"])))
        target_date = issue_date + pd.Timedelta(days=horizon)

        fig, axes = plt.subplots(1, 3, figsize=(15, 4.25), facecolor="#f8fafc")

        observed = axes[0].pcolormesh(
            grid_lon, grid_lat, actual_grid,
            cmap="viridis", vmin=CHL_VMIN, vmax=CHL_VMAX, shading="auto",
        )
        axes[0].scatter(day.longitude, day.latitude, c="white", s=2, alpha=0.38)
        axes[0].set_title(f"Observed target · {target_date.date()}")
        axes[0].set_ylabel("Latitude")
        plt.colorbar(observed, ax=axes[0], label="log10 mg m⁻³")

        predicted = axes[1].pcolormesh(
            grid_lon, grid_lat, predicted_grid,
            cmap="viridis", vmin=CHL_VMIN, vmax=CHL_VMAX, shading="auto",
        )
        axes[1].set_title(f"Predicted · issued {issue_date.date()} · H+{horizon}")
        plt.colorbar(predicted, ax=axes[1], label="log10 mg m⁻³")

        residual = axes[2].pcolormesh(
            grid_lon, grid_lat, residual_grid,
            cmap="RdBu_r", vmin=-RES_LIM, vmax=RES_LIM, shading="auto",
        )
        axes[2].set_title(f"Residual · prediction − observation · MAE {sampled_mae:.3f}")
        plt.colorbar(residual, ax=axes[2], label="log10")

        for axis in axes:
            axis.set_xlabel("Longitude")
            axis.set_facecolor("#e2e8f0")

        fig.suptitle(
            f"Final v2 single-split diagnostic · {len(day):,} observed target rows",
            fontsize=11,
            color="#334155",
        )
        plt.tight_layout(rect=(0, 0, 1, 0.95))

        png_path = horizon_dir / f"frame_{frame_index:03d}.png"
        webp_path = png_path.with_suffix(".webp")
        fig.savefig(png_path, dpi=DPI, bbox_inches="tight")
        plt.close(fig)
        with Image.open(png_path) as image:
            image.convert("RGB").save(webp_path, "WEBP", quality=80, method=6)
        png_path.unlink()

        maes.append(round(sampled_mae, 5))
        row_counts.append(int(len(day)))

    mae_by_horizon[str(horizon)] = maes
    rows_by_horizon[str(horizon)] = row_counts
    print(f"H+{horizon}: wrote {N_DATES} frames")

manifest = {
    "model": "XGBoost v2 single-split diagnostic",
    "feature_count": len(feature_cols),
    "horizons": HORIZONS,
    "issue_dates": [str(date.date()) for date in selected_dates],
    "n_frames": N_DATES,
    "frame_pattern": "figs/pred_frames/h{h}/frame_{idx:03d}.webp",
    "mae_by_horizon": mae_by_horizon,
    "rows_by_horizon": rows_by_horizon,
    "interpolation": "Linear interpolation of sampled test rows for visualization only; masked outside the convex hull.",
    "evaluation_note": "Metrics use original sampled rows. Raster pixels are not additional evaluated observations.",
}

(OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Wrote {N_DATES * len(HORIZONS)} frames in {time.time() - started:.1f}s")

