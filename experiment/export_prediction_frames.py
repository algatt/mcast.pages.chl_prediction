"""Export dense Actual|Predicted|Residual map frames for the website slider.

Reproduces the logic of Notebook 07 cells 7.7a/7.7b/7.7c (the "dense player"),
then writes one PNG per (day, horizon) plus a manifest.json that the Vue
PredictionPlayer component consumes.

Run from the experiment/ directory with the project venv:
    .venv/Scripts/python.exe experiment/export_prediction_frames.py
"""
from pathlib import Path
import json
import time as pytime

import numpy as np
import pandas as pd
import xgboost as xgb
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- config
EXPORT_HORIZONS = [1, 3, 7]          # which horizons the slider offers
DPI = 90                              # keep frames light for GitHub Pages
CHL_VMIN, CHL_VMAX = -2.0, 0.5        # log10 mg/m^3, fixed so frames compare
RES_LIM = 0.5                         # +/- log10 residual colour limit

HERE = Path(__file__).resolve().parent
PROC_DIR = HERE / "data" / "processed"
MODEL_DIR = HERE / "models"
RAW = HERE / "data" / "raw"
OUT_DIR = HERE.parent / "website" / "public" / "figs" / "pred_frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- setup (cell 2)
df = pd.read_parquet(PROC_DIR / "supervised_sample.parquet").sort_values("time").reset_index(drop=True)
manifest = json.load(open(PROC_DIR / "feature_manifest.json"))
FEATURE_COLS = manifest["feature_cols"]
HORIZONS = manifest["horizons"]

cut_val = df["time"].quantile(0.85)
test = df[df.time > cut_val].copy()

models = {}
for h in EXPORT_HORIZONS:
    m = xgb.XGBRegressor()
    m.load_model(MODEL_DIR / f"xgb_h{h}.json")
    models[h] = m
print(f"Loaded models for horizons {EXPORT_HORIZONS}; test rows {len(test):,}")

# ---------------------------------------------------------------- feature cube (cell 21)
t0 = pytime.time()
chl_ds = xr.open_dataset(RAW / "chl_malta_2021_2023.nc")
sst_ds = xr.open_dataset(RAW / "sst_malta_2021_2023.nc")
bathy_ds = xr.open_dataset(RAW / "bathy_malta.nc")

chl = chl_ds["CHL"]
sst = sst_ds["analysed_sst"]
if float(sst.isel(time=0).max()) > 200:
    sst = sst - 273.15
elev_var = next(v for v in bathy_ds.data_vars if v in ("z", "elevation", "bed_elevation"))
elev = bathy_ds[elev_var]
depth = -elev.where(elev < 0, 0)
log_chl = np.log10(chl).rename("log_chl")

sst_on_chl = sst.interp(latitude=chl.latitude, longitude=chl.longitude)
depth_on_chl = depth.interp(latitude=chl.latitude, longitude=chl.longitude)
sst_on_chl = sst_on_chl.reindex(time=chl.time, method="nearest",
                                tolerance=np.timedelta64(1, "D"))

TEST_START = pd.Timestamp(test["time"].min())
slice_start = TEST_START - pd.Timedelta(days=20)
log_chl_slc = log_chl.sel(time=slice(slice_start, None))
sst_slc = sst_on_chl.sel(time=slice(slice_start, None))

feat = xr.Dataset()
feat["log_chl_t0"] = log_chl_slc
for lag in [1, 2, 3, 7, 14]:
    feat[f"log_chl_lag{lag}"] = log_chl_slc.shift(time=lag)
feat["log_chl_roll7_mean"] = log_chl_slc.rolling(time=7, min_periods=1).mean()
feat["log_chl_roll7_std"] = log_chl_slc.rolling(time=7, min_periods=2).std()
feat["sst_t0"] = sst_slc
feat["sst_lag1"] = sst_slc.shift(time=1)
feat["sst_roll7_mean"] = sst_slc.rolling(time=7, min_periods=1).mean()
feat["depth_m"] = depth_on_chl.broadcast_like(log_chl_slc)
doy = log_chl_slc.time.dt.dayofyear
feat["doy_sin"] = np.sin(2 * np.pi * doy / 365.25).broadcast_like(log_chl_slc)
feat["doy_cos"] = np.cos(2 * np.pi * doy / 365.25).broadcast_like(log_chl_slc)

valid = (~np.isnan(log_chl_slc.values)).astype(np.int32)
gap_age_arr = np.empty_like(valid)
gap_age_arr[0] = 0
for tt in range(1, valid.shape[0]):
    gap_age_arr[tt] = np.where(valid[tt], 0, gap_age_arr[tt - 1] + 1)
feat["gap_age"] = xr.DataArray(gap_age_arr, dims=log_chl_slc.dims, coords=log_chl_slc.coords)

feat_test = feat.sel(time=slice(TEST_START, None))
print(f"Feature cube: {dict(feat_test.sizes)}  ({pytime.time()-t0:.1f}s)")

# ---------------------------------------------------------------- predict grids (cell 22)
n_time, n_lat, n_lon = feat_test.sizes["time"], feat_test.sizes["latitude"], feat_test.sizes["longitude"]
n_rows = n_time * n_lat * n_lon
X_flat = np.stack([feat_test[c].values.reshape(n_rows) for c in FEATURE_COLS], axis=1)

pred_grids, actual_grids = {}, {}
for h in EXPORT_HORIZONS:
    p = models[h].predict(X_flat).astype(np.float32)
    pred_grids[h] = xr.DataArray(
        p.reshape(n_time, n_lat, n_lon),
        dims=("time", "latitude", "longitude"),
        coords={"time": feat_test.time, "latitude": feat_test.latitude, "longitude": feat_test.longitude},
    )
    actual_grids[h] = log_chl.shift(time=-h).sel(time=feat_test.time)
print(f"Predicted grids for {EXPORT_HORIZONS}  ({pytime.time()-t0:.1f}s)")

# ---------------------------------------------------------------- optional L4 reference
# The gap-free L4 (DINEOF) product, if downloaded, gives a hole-free "actual"
# field. It is a COMPARISON reference, not ground truth: L4 is itself an
# interpolation, so error-vs-L4 measures agreement with the conventional product,
# while error-vs-L3 (observed) remains the honest score.
L4_PATH = RAW / "chl_l4_malta_test2023.nc"
actual_grids_l4 = None
if L4_PATH.exists():
    l4 = xr.open_dataset(L4_PATH)["CHL"]
    log_chl_l4 = np.log10(l4).rename("log_chl_l4")
    actual_grids_l4 = {h: log_chl_l4.shift(time=-h).reindex(time=feat_test.time) for h in EXPORT_HORIZONS}
    print(f"L4 reference loaded from {L4_PATH.name}")
else:
    print("No L4 file found — skipping L4 reference frames.")

# ---------------------------------------------------------------- render frames
grid_dates = feat_test.time.values
dates_iso = [str(pd.Timestamp(t).date()) for t in grid_dates]
from PIL import Image


def render_set(actual_grids_ref, subdir, ref_label):
    """Render Actual|Predicted|Error frames for one reference field. Returns
    {horizon: [mae-or-None, ...]}."""
    mae_out = {}
    for h in EXPORT_HORIZONS:
        hdir = OUT_DIR / f"h{h}" / subdir if subdir else OUT_DIR / f"h{h}"
        hdir.mkdir(parents=True, exist_ok=True)
        maes = []
        for idx in range(len(grid_dates)):
            actual = actual_grids_ref[h].isel(time=idx)
            pred = pred_grids[h].isel(time=idx)
            residual = pred - actual
            mae = float(np.abs(residual).mean())
            # Fully-missing days have an undefined MAE; emit null (not NaN,
            # which is invalid JSON and breaks JSON.parse in the browser).
            maes.append(round(mae, 4) if np.isfinite(mae) else None)
            cov = float(actual.notnull().mean())

            fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
            im0 = axes[0].pcolormesh(actual.longitude, actual.latitude, actual,
                                     cmap="viridis", vmin=CHL_VMIN, vmax=CHL_VMAX, shading="auto")
            axes[0].set_title(f"Actual ({ref_label})  {dates_iso[idx]} +{h}d  (coverage {cov*100:.0f}%)")
            axes[0].set_xlabel("Longitude"); axes[0].set_ylabel("Latitude")
            plt.colorbar(im0, ax=axes[0], label="log10 mg m-3")

            im1 = axes[1].pcolormesh(pred.longitude, pred.latitude, pred,
                                     cmap="viridis", vmin=CHL_VMIN, vmax=CHL_VMAX, shading="auto")
            axes[1].set_title(f"Predicted  H+{h} (every pixel)")
            axes[1].set_xlabel("Longitude")
            plt.colorbar(im1, ax=axes[1], label="log10 mg m-3")

            im2 = axes[2].pcolormesh(residual.longitude, residual.latitude, residual,
                                     cmap="RdBu_r", vmin=-RES_LIM, vmax=RES_LIM, shading="auto")
            axes[2].set_title(f"Error (pred - {ref_label})  MAE={mae:.3f}")
            axes[2].set_xlabel("Longitude")
            plt.colorbar(im2, ax=axes[2], label="log10")

            plt.tight_layout()
            # Save via WebP (~80% smaller than PNG) to keep the static-site payload light.
            _p = hdir / f"frame_{idx:03d}.png"
            fig.savefig(_p, dpi=DPI)
            Image.open(_p).convert("RGB").save(_p.with_suffix(".webp"), "WEBP", quality=80, method=6)
            _p.unlink()
            plt.close(fig)
        mae_out[str(h)] = maes
        print(f"  [{ref_label}] H+{h}: wrote {len(grid_dates)} frames")
    return mae_out


mae_by_h = render_set(actual_grids, "", "L3 obs")

manifest_out = {
    "horizons": EXPORT_HORIZONS,
    "dates": dates_iso,
    "n_frames": len(grid_dates),
    "frame_pattern": "figs/pred_frames/h{h}/frame_{idx:03d}.webp",
    "mae_by_horizon": mae_by_h,
    "has_l4": False,
    "notes": "Dense per-pixel forecast. Left=actual, mid=predicted, right=error (pred-actual).",
}

if actual_grids_l4 is not None:
    mae_l4 = render_set(actual_grids_l4, "l4", "L4 gap-free")
    manifest_out["has_l4"] = True
    manifest_out["frame_pattern_l4"] = "figs/pred_frames/h{h}/l4/frame_{idx:03d}.webp"
    manifest_out["mae_l4_by_horizon"] = mae_l4

json.dump(manifest_out, open(OUT_DIR / "manifest.json", "w"), indent=2, allow_nan=False)
print(f"Wrote manifest.json with {len(grid_dates)} dates. Done in {pytime.time()-t0:.1f}s")
