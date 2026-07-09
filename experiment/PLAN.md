# Chlorophyll-a Forecasting & Bloom Detection — Malta–Sicily Channel
## A Step-by-Step Implementation Guide (with Validation Stages)

> **How to use this guide.** Work top to bottom. Each stage has a **goal**, **runnable code**, and a **✅ Validation gate** you must pass before moving on. The gates are the point: they stop you carrying a silent error into the next stage. Tick the `- [ ]` boxes as you go.
>
> **Environment:** local laptop, Python 3.11+. **Region box:** 35.5–37.5°N, 12.0–15.5°E. **Target:** daily L3 chlorophyll-a, forecast horizons T+1…T+7, plus bloom-event detection.
>
> **Philosophy reminder:** we deliberately use **non-interpolated L3** for the **target** (chlorophyll-a) and let gaps stay as `NaN`. Never silently fill them — that is the whole novelty. Every stage respects that.
>
> **Target vs predictors — an important distinction.** The no-interpolation rule applies to the *thing you predict*. For **predictors** (wind, waves, salinity, currents, mixed-layer depth, etc.) it is standard and methodologically sound to use **reanalysis / model analysis fields**, which are gap-free by construction. Those variables simply have no daily observational L3 equivalent, and using a modelled field as an *input* creates no circularity because the model is never scored on reproducing it. State this explicitly in your methods: *"Target: non-interpolated L3 ocean colour. Predictors: a mix of L3 observations (SST) and reanalysis/analysis fields (wind, waves, salinity, currents, MLD)."* The **one** thing to avoid is feeding a biogeochemical *model's* chlorophyll in as a predictor for your observed-chlorophyll target — that *would* be circular. Skip `chl` from the BGC model; its nutrients/oxygen are fine.

---

## Stage 0 — Environment setup

**Goal:** a reproducible environment and a verified CMEMS login.

- [ ] Create and activate a virtual environment
- [ ] Install dependencies
- [ ] Store CMEMS credentials
- [ ] Verify the toolbox can see the catalogue

```bash
# 0.1 — virtual env
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip

# 0.2 — dependencies
pip install "copernicusmarine>=2.4.1" xarray netCDF4 dask zarr \
            numpy pandas scikit-learn xgboost lightgbm \
            matplotlib cartopy shap cdsapi tqdm pyarrow
```

```bash
# 0.3 — credentials (run once; stores a token file in your home dir)
copernicusmarine login
# You'll be prompted for your Copernicus Marine username + password.
# Register free at https://data.marine.copernicus.eu if you don't have an account.
```

```python
# 0.4 — verify (save as check_env.py and run it)
import copernicusmarine, xarray, xgboost, lightgbm, sklearn
print("copernicusmarine:", copernicusmarine.__version__)
print("xarray:", xarray.__version__)
print("xgboost:", xgboost.__version__)

# Confirm the catalogue is reachable and the dataset ID exists
ds_meta = copernicusmarine.describe(
    dataset_id="cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D"
)
print("Catalogue reachable — dataset found.")
```

### ✅ Validation gate 0
- [ ] `check_env.py` prints version numbers with **no import errors**
- [ ] `describe(...)` returns metadata (no auth or network error)
- [ ] You understand *why* we picked the `*_my_l3-multi-1km_P1D` dataset (multi-sensor merge, 1997–present, no temporal interpolation)

> **If it fails:** auth errors → re-run `copernicusmarine login`. Network errors → check firewall/proxy. Dataset-not-found → the ID may have been versioned; run `copernicusmarine describe --contains "med_bgc-plankton"` to list current IDs.

---

## Stage 1 — Data acquisition (chlorophyll target)

**Goal:** pull the L3 chl-a cube for the region box and a sensible test period. Start **small** (3 years) to keep iteration fast; scale up later.

- [ ] Subset the multi-sensor 1 km L3 product to the box
- [ ] Save to local NetCDF
- [ ] Open it and inspect structure

```python
# 1.1 — download_chl.py
import copernicusmarine

BOX = dict(minimum_longitude=12.0, maximum_longitude=15.5,
           minimum_latitude=35.5,  maximum_latitude=37.5)

copernicusmarine.subset(
    dataset_id="cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D",
    variables=["CHL"],                     # add "CHL_uncertainty" if present
    start_datetime="2021-01-01T00:00:00",
    end_datetime="2023-12-31T00:00:00",
    output_filename="chl_malta_2021_2023.nc",
    output_directory="data/raw",
    **BOX,
)
```

```python
# 1.2 — inspect.py
import xarray as xr
ds = xr.open_dataset("data/raw/chl_malta_2021_2023.nc")
print(ds)
print("\nDims:", dict(ds.sizes))
print("Time range:", ds.time.values.min(), "→", ds.time.values.max())
print("CHL units:", ds.CHL.attrs.get("units"))
```

### ✅ Validation gate 1
- [ ] File `data/raw/chl_malta_2021_2023.nc` exists and is non-trivial in size (hundreds of MB is normal)
- [ ] `ds` has dims **time, latitude, longitude**; ~1095 time steps for 3 years
- [ ] Latitude/longitude spans match the box (≈ 35.5–37.5, 12.0–15.5)
- [ ] CHL has plenty of `NaN`s — **this is expected and correct** (cloud gaps). If there are *no* NaNs, you accidentally grabbed an L4 product — stop and recheck the dataset ID.

> **Sanity check the numbers:** open-Mediterranean surface CHL is typically **0.05–0.5 mg m⁻³**. Run `float(ds.CHL.median())` — a median in roughly that range means the retrieval is sane. A median of 5 or 50 means wrong units or wrong product.

---

## Stage 2 — Gap-coverage atlas (the most important diagnostic)

**Goal:** quantify how cloudy your data really is, **per month**. This single diagnostic decides whether daily forecasting is viable or whether you must drop to 3-day composites. Do not skip it.

- [ ] Compute valid-pixel fraction per day
- [ ] Aggregate to a monthly climatology of coverage
- [ ] Plot it and read the winter months

```python
# 2.1 — coverage_atlas.py
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

ds = xr.open_dataset("data/raw/chl_malta_2021_2023.nc")
chl = ds.CHL

# valid-pixel fraction per timestep
n_pixels = chl.isel(time=0).size
valid_frac = chl.notnull().sum(dim=["latitude", "longitude"]) / n_pixels
valid_frac = valid_frac.to_series()

# monthly mean coverage
monthly = valid_frac.groupby(valid_frac.index.month).mean()

print("Mean daily valid-pixel fraction by month:")
print((monthly * 100).round(1).rename("coverage_%"))

plt.figure(figsize=(8, 4))
(monthly * 100).plot(kind="bar")
plt.axhline(25, color="red", linestyle="--", label="25% decision threshold")
plt.ylabel("Valid-pixel coverage (%)")
plt.xlabel("Month")
plt.title("L3 daily coverage — Malta–Sicily Channel")
plt.legend(); plt.tight_layout()
plt.savefig("figs/coverage_atlas.png", dpi=150)
print("Saved figs/coverage_atlas.png")
```

### ✅ Validation gate 2 — **this gate has a branch**
- [ ] `figs/coverage_atlas.png` is saved and readable
- [ ] You have written down the **winter (Dec–Feb) coverage %**

**Decision branch (from the research plan):**
- **If Dec–Feb mean coverage ≥ 25%** → proceed with **daily** forecasting as planned.
- **If Dec–Feb mean coverage < 25%** → switch your target to a **3-day rolling composite** now (add `.rolling(time=3, min_periods=1).mean()` when you build the target in Stage 4). Note this decision in your lab log — it's a legitimate, defensible methodological choice, not a compromise.

> **Why this matters:** winter convective blooms happen *in exactly the cloudiest season*. If you discover coverage is poor only after training models, you'll have wasted weeks. Front-load the pain here.

---

## Stage 3 — Covariate acquisition (predictors)

**Goal:** pull the physical drivers. **For the first end-to-end loop, download only SST + bathymetry** and get the whole pipeline working. The full roster of predictors (wind, waves, salinity, currents, MLD, optics) is added later in Stage 8 — resist grabbing everything now, or you'll spend days wrangling data before you know the pipeline even runs.

- [ ] Download L3 SST for the same box & period
- [ ] Download EMODnet/GEBCO bathymetry for the box
- [ ] Read the predictor roster below (but defer downloading the rest to Stage 8)

```python
# 3.1 — download_sst.py
import copernicusmarine
BOX = dict(minimum_longitude=12.0, maximum_longitude=15.5,
           minimum_latitude=35.5,  maximum_latitude=37.5)

copernicusmarine.subset(
    dataset_id="cmems_obs-sst_med_phy_l3s_my_P1D-m",   # CONFIRM — see note
    variables=["adjusted_sea_surface_temperature"],
    start_datetime="2021-01-01T00:00:00",
    end_datetime="2023-12-31T00:00:00",
    output_filename="sst_malta_2021_2023.nc",
    output_directory="data/raw",
    **BOX,
)
```

> **Note on the SST dataset ID.** Use the Mediterranean L3S SST product (family `SST_MED_PHY_L3S_MY_010_042`). Confirm the exact current granular `dataset_id` with `copernicusmarine describe --contains "SST_MED"` — the short-name string is versioned and may differ from the line above. Pull `adjusted_sea_surface_temperature` (L3S, gappy) or use the gap-free L4 `SST_MED_SST_L4_REP_OBSERVATIONS_010_021` if you'd rather a complete SST field as a predictor.

```python
# 3.2 — bathymetry: EMODnet DTM 2024 (central Med tile) from
# https://emodnet.ec.europa.eu/en/bathymetry  — OR GEBCO 2024 as a quick fallback:
import xarray as xr
gebco = xr.open_dataset("data/raw/GEBCO_2024.nc")   # downloaded separately
bathy = gebco.sel(lon=slice(12.0, 15.5), lat=slice(35.5, 37.5))
bathy.to_netcdf("data/raw/bathy_malta.nc")
print("Bathymetry subset saved.")
```

### Predictor roster — the full covariate stack (download these in Stage 8)

> ⚠️ **All dataset IDs below must be confirmed before use.** CMEMS versions its product and dataset short-names periodically. For each one, run `copernicusmarine describe --contains "<PRODUCT_FAMILY>"` and copy the exact granular `dataset_id`. The **product family IDs** (the long UPPERCASE codes) are stable and are your search anchor; the lowercase `dataset_id` strings drift. Treat the strings below as *starting points*, not gospel.

**Note on `MY` vs `NRT`/analysis-forecast:** use the **MY (multi-year reanalysis)** products for the historical training record, and switch to the **analysis-forecast** twin for operational T+1…T+7 inference — exactly the same pattern as the chl-a target (009_143 for history, 009_141 for NRT).

| Group | Product family (stable anchor) | Granular `dataset_id` (CONFIRM) | Resolution | Coverage | Key variables |
|---|---|---|---|---|---|
| **Wind — reanalysis** | ERA5 single levels (CDS) | via `cdsapi` (not CMEMS) | ~31 km, hourly | 1940– | `10m_u/v_component_of_wind`, MSLP, radiation |
| **Wind — satellite L3** | `WIND_GLO_PHY_L3_MY_012_005` (NRT twin: `_NRT_012_002`) | `cmems_obs-wind_glo_phy_my_l3_*` | ~12.5–25 km, swath/daily | 2007– (ASCAT) | `eastward_wind`, `northward_wind`, `wind_speed`, `wind_stress` |
| **Waves** | `MEDSEA_MULTIYEAR_WAV_006_012` (AF twin: `MEDSEA_ANALYSISFORECAST_WAV_006_017`) | `cmems_mod_med_wav_my_*_P1D-m` | ~1/24° (~4 km), hourly→daily | 1985– | `VHM0` (sig. wave height), `VTM02`/`VTPK` (period), `VMDR` (direction), swell partitions |
| **Salinity + currents + SSH + temp@depth + MLD** | `MEDSEA_MULTIYEAR_PHY_006_004` (AF twin: `MEDSEA_ANALYSISFORECAST_PHY_006_013`) | `cmems_mod_med_phy-sal_my_*`, `…phy-cur…`, `…phy-ssh…`, `…phy-tem…`, `…phy-mld…` | ~1/24° (~4 km), daily | 1987– | `so` (salinity), `uo`/`vo` (currents), `zos` (SSH), `thetao` (temp@depth), `mlotst` (MLD) |
| **Sea level / geostrophy (AIS proxy)** | `SEALEVEL_EUR_PHY_L4_MY_008_068` (or global `008_047`) | `cmems_obs-sl_eur_phy-ssh_my_*_P1D` | ~1/8°, daily | 1993– | `sla`, `adt`, `ugos`, `vgos` (geostrophic velocity) |
| **Optics / transparency** | within `OCEANCOLOUR_MED_BGC_L3_MY_009_143` | `…-optics_my_l3-multi-1km_P1D`, `…-transp_my_l3-multi-1km_P1D` | 1 km, daily | 1997– | `KD490`, `PAR`, `BBP`, `ADG`, `APH` |
| **Biogeochemistry (optional)** | `MEDSEA_MULTIYEAR_BGC_006_008` (AF twin: `MEDSEA_ANALYSISFORECAST_BGC_006_014`) | `cmems_mod_med_bgc-nut_my_*`, `…bgc-bio…` | ~1/24°, daily | 1999– | `no3`, `po4`, `o2`, `nppv`, `ph` — **NOT `chl`** (would be circular) |

**On wind specifically (ERA5 vs ASCAT):** ERA5 is a *reanalysis* — complete, gap-free, hourly, ~31 km, modelled (smoothed, weaker coastal gradients). ASCAT is a *scatterometer* — a more direct measurement at ~12.5–25 km, but only along satellite swaths, with twice-daily passes and a **coastal blind zone (~15–30 km from land)** that bites in the narrow Maltese strip. **Use ERA5 as the workhorse** (every day populated) and **ASCAT as an enrichment/validation layer**, not a replacement.

### ✅ Validation gate 3
- [ ] SST cube downloaded; same box, overlapping dates with CHL
- [ ] SST values are sane (Mediterranean SST ≈ **13–28 °C** by season; if in Kelvin, ≈ 286–301)
- [ ] Bathymetry subset covers the box; depths are **negative** (below sea level) or you know the sign convention
- [ ] All three cubes (CHL, SST, bathy) share the **same lon/lat conventions** (ascending vs descending latitude — check `bathy.lat.values[0]` vs `ds.latitude.values[0]`)
- [ ] You've located the predictor roster but have **not** downloaded the full stack yet (that's Stage 8 — keep the first loop lean)

---

## Stage 4 — Build the supervised dataset (the careful part)

**Goal:** turn gridded cubes into a tidy table of `(features at time t) → (CHL at t+h)`, keeping gaps as `NaN`. This is where most silent bugs are born, so validate hard.

- [ ] Regrid SST & bathy onto the CHL grid
- [ ] Engineer lag, rolling, gap-age, SST, static and temporal features
- [ ] Create one target column per horizon h ∈ {1..7}
- [ ] Flatten to a DataFrame with a proper time index
- [ ] **Sample** pixels (don't use all ~10⁷ rows yet)

```python
# 4.1 — build_dataset.py
import xarray as xr
import numpy as np
import pandas as pd

chl_ds  = xr.open_dataset("data/raw/chl_malta_2021_2023.nc")
sst_ds  = xr.open_dataset("data/raw/sst_malta_2021_2023.nc")
bathy   = xr.open_dataset("data/raw/bathy_malta.nc")

chl = np.log10(chl_ds.CHL)          # model in log10 space (ocean-colour standard)
chl.name = "log_chl"

# --- align SST & bathy onto the CHL grid ---
sst = sst_ds["adjusted_sea_surface_temperature"].interp(
    latitude=chl.latitude, longitude=chl.longitude)         # spatial only
bathy_i = bathy["elevation"].interp(
    lat=chl.latitude, lon=chl.longitude).rename({"lat": "latitude", "lon": "longitude"})

# --- lag & rolling features on the target (gap-aware) ---
feat = xr.Dataset()
feat["log_chl_t0"]   = chl
for lag in [1, 2, 3, 7, 14]:
    feat[f"log_chl_lag{lag}"] = chl.shift(time=lag)
feat["log_chl_roll7_mean"] = chl.rolling(time=7, min_periods=1).mean()
feat["log_chl_roll7_std"]  = chl.rolling(time=7, min_periods=2).std()

# gap-age: days since last valid CHL observation, per pixel
valid = chl.notnull()
# cumulative count that resets on each valid obs:
ages = []
last = xr.full_like(chl.isel(time=0), np.nan)
age  = xr.zeros_like(chl.isel(time=0))
for t in range(chl.sizes["time"]):
    v = valid.isel(time=t)
    age = xr.where(v, 0, age + 1)
    ages.append(age.copy())
feat["gap_age"] = xr.concat(ages, dim=chl.time)

# SST features
feat["sst_t0"]   = sst
feat["sst_lag1"] = sst.shift(time=1)
feat["sst_roll7_mean"] = sst.rolling(time=7, min_periods=1).mean()

# static
feat["bathy"] = bathy_i.broadcast_like(chl)

# temporal encodings
doy = chl.time.dt.dayofyear
feat["doy_sin"] = np.sin(2*np.pi*doy/365.25).broadcast_like(chl)
feat["doy_cos"] = np.cos(2*np.pi*doy/365.25).broadcast_like(chl)

# --- targets: CHL at t+h ---
targets = {}
for h in range(1, 8):
    targets[f"target_h{h}"] = chl.shift(time=-h)

# --- flatten to DataFrame ---
df = feat.to_dataframe()
for k, v in targets.items():
    df[k] = v.to_dataframe()[v.name]

df = df.reset_index()    # columns: time, latitude, longitude, + features + targets
print("Full long table shape:", df.shape)

# --- sample to keep it tractable (stratify by month to keep seasonality) ---
df["month"] = df["time"].dt.month
sample = (df.dropna(subset=["log_chl_t0"])             # need a valid 'now' obs
            .groupby("month", group_keys=False)
            .apply(lambda g: g.sample(min(len(g), 40000), random_state=42)))
sample.to_parquet("data/processed/supervised_sample.parquet")
print("Sampled table shape:", sample.shape)
```

### ✅ Validation gate 4 — **validate this stage hardest**
- [ ] **Leakage check:** `target_h1` at time *t* must equal `log_chl_t0` at time *t+1* for the same pixel. Verify on one pixel:
  ```python
  # leakage_check.py
  p = df[(df.latitude==df.latitude.iloc[1000]) &
         (df.longitude==df.longitude.iloc[1000])].sort_values("time")
  assert np.allclose(
      p["target_h1"].values[:-1],
      p["log_chl_t0"].values[1:],
      equal_nan=True), "TARGET MISALIGNED — fix the shift before continuing"
  print("Leakage/alignment check passed.")
  ```
- [ ] Lags go **backward** (`shift(time=+lag)`) and targets go **forward** (`shift(time=-h)`). Mixing these is the classic catastrophic bug.
- [ ] Feature rows retain `NaN`s (you only dropped rows lacking a valid *current* observation, not rows with missing lags) — confirm `sample.isna().mean()` shows non-zero NaN fractions in lag columns
- [ ] `gap_age` is 0 wherever `log_chl_t0` is valid, and increments where it's missing
- [ ] No `target_h*` column is entirely NaN

> **The single most important check in the whole project is the leakage assert above.** If targets and features are misaligned by even one step, you'll get an impressive-looking R² that is pure leakage. Run it. Trust it.

---

## Stage 5 — Baseline models you must beat

**Goal:** establish **persistence** and **climatology** baselines. A fancy model that can't beat persistence is worthless, and you can only know that if you compute persistence first.

- [ ] Persistence: predict CHL(t+h) = CHL(t)
- [ ] Climatology: predict the day-of-year mean
- [ ] Record their RMSE/R² per horizon

```python
# 5.1 — baselines.py
import pandas as pd, numpy as np
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_parquet("data/processed/supervised_sample.parquet")

def score(y_true, y_pred):
    m = y_true.notna() & pd.Series(y_pred, index=y_true.index).notna()
    return dict(rmse=mean_squared_error(y_true[m], np.asarray(y_pred)[m.values])**0.5,
                r2=r2_score(y_true[m], np.asarray(y_pred)[m.values]),
                n=int(m.sum()))

for h in range(1, 8):
    y = df[f"target_h{h}"]
    persistence = df["log_chl_t0"].values          # naive: tomorrow = today
    print(f"H+{h} persistence:", score(y, persistence))
```

### ✅ Validation gate 5
- [ ] Persistence R² is recorded for **every** horizon (it should be high at H+1 and decay toward H+7)
- [ ] You have a written target: **your ML model must beat persistence at H+3 and beyond** (at H+1 persistence is often very hard to beat — that's normal and fine)
- [ ] You understand that beating persistence, not hitting a magic R², is the real bar

---

## Stage 6 — Tree-based model with a CHRONOLOGICAL split

**Goal:** train XGBoost per horizon using native NaN handling and a **strict time-ordered** split. No random shuffling — ever — in time series.

- [ ] Split by **time**, not randomly
- [ ] Train one XGBoost per horizon
- [ ] Compare against persistence from Stage 5

```python
# 6.1 — train_xgb.py
import pandas as pd, numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_parquet("data/processed/supervised_sample.parquet").sort_values("time")

feature_cols = [c for c in df.columns
                if c.startswith(("log_chl_lag","log_chl_roll","gap_age",
                                 "sst_","bathy","doy_")) or c == "log_chl_t0"]

# --- CHRONOLOGICAL split ---
cut_train = df["time"].quantile(0.70)
cut_val   = df["time"].quantile(0.85)
tr = df[df.time <= cut_train]
va = df[(df.time > cut_train) & (df.time <= cut_val)]
te = df[df.time > cut_val]
print(f"train {tr.time.min().date()}–{tr.time.max().date()} | "
      f"val …{va.time.max().date()} | test …{te.time.max().date()}")

results = {}
for h in range(1, 8):
    tgt = f"target_h{h}"
    Xtr, ytr = tr[feature_cols], tr[tgt]
    Xva, yva = va[feature_cols], va[tgt]
    Xte, yte = te[feature_cols], te[tgt]

    mtr = ytr.notna(); mva = yva.notna(); mte = yte.notna()

    model = xgb.XGBRegressor(
        n_estimators=600, max_depth=6, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8,
        missing=np.nan,                 # native NaN handling — the whole point
        early_stopping_rounds=40, eval_metric="rmse", n_jobs=-1)
    model.fit(Xtr[mtr], ytr[mtr],
              eval_set=[(Xva[mva], yva[mva])], verbose=False)

    pred = model.predict(Xte[mte])
    rmse = mean_squared_error(yte[mte], pred)**0.5
    r2   = r2_score(yte[mte], pred)
    results[h] = (rmse, r2)
    model.save_model(f"models/xgb_h{h}.json")
    print(f"H+{h}: RMSE={rmse:.3f}  R2={r2:.3f}")
```

### ✅ Validation gate 6
- [ ] Train/val/test are **time-ordered and non-overlapping** (printed dates confirm it)
- [ ] Test R² at **H+1** is in a believable range (roughly 0.6–0.85 on log-CHL); wildly higher (>0.95) usually means leakage — revisit Gate 4
- [ ] Your model **beats persistence** at H+3+ (compare to Stage 5 numbers). If it doesn't, the model adds nothing yet — check features before adding complexity.
- [ ] R² **decays** from H+1 to H+7 (a flat or rising curve across horizons is a red flag)

> **Compare to your prior work deliberately.** Your earlier L4-based pipeline hit R² ≈ 0.85. The scientific result here is the **delta** between that and this L3 result. A *somewhat* lower R² on raw L3 is expected and is itself a finding — don't chase the old number by sneaking in interpolation.

---

## Stage 7 — Interpretability & error diagnostics

**Goal:** understand *why* the model predicts what it does, and *where* it fails. This is what turns a script into research.

- [ ] SHAP feature importance for H+1 and H+7
- [ ] Error maps by sub-region and season
- [ ] Residual checks

```python
# 7.1 — interpret.py
import shap, xgboost as xgb, pandas as pd, numpy as np
df = pd.read_parquet("data/processed/supervised_sample.parquet")
feature_cols = [c for c in df.columns
                if c.startswith(("log_chl_lag","log_chl_roll","gap_age",
                                 "sst_","bathy","doy_")) or c == "log_chl_t0"]
model = xgb.XGBRegressor(); model.load_model("models/xgb_h1.json")

sample = df[feature_cols].sample(5000, random_state=0)
explainer = shap.TreeExplainer(model)
sv = explainer.shap_values(sample)
shap.summary_plot(sv, sample, show=False)
import matplotlib.pyplot as plt; plt.tight_layout()
plt.savefig("figs/shap_h1.png", dpi=150)
```

### ✅ Validation gate 7
- [ ] SHAP plot saved; the top features are **physically plausible** (recent CHL lags and SST should dominate; if `doy_sin` alone dominates, the model is just learning the seasonal cycle — add dynamic features)
- [ ] Error is mapped by season — confirm whether **winter** error is worst (expected, per the coverage atlas)
- [ ] Residuals show no strong trend vs. predicted value (heteroscedasticity is OK to note; structure suggests a missing feature)

---

## Stage 8 — Add the full covariate stack & handle correlated predictors

**Goal:** now that the loop works end-to-end, bring in the rest of the predictor roster (wind, waves, salinity, currents, SSH, MLD, optics), regrid everything onto the chl-a grid, and use a disciplined **"add all, then let importance + ablation decide"** strategy — handling the trap that correlated predictors split and disguise each other's importance.

- [ ] Download ERA5 wind + the CMEMS physics/waves/optics stack (Stage 3 roster)
- [ ] Regrid all predictors onto the 1 km chl-a grid
- [ ] Add them all as features, **grouped by theme**
- [ ] Check a correlation matrix *before* trusting any importance
- [ ] Read importance by **group**, then **ablate by group** to confirm
- [ ] Keep only groups that earn their place on validation score

### 8.1 — Download the rest of the stack

```python
# 8.1a — ERA5 wind via cdsapi (configure ~/.cdsapirc first; register at CDS)
import cdsapi
c = cdsapi.Client()
c.retrieve("reanalysis-era5-single-levels", {
    "product_type": "reanalysis",
    "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
    "year": ["2021","2022","2023"],
    "month": [f"{m:02d}" for m in range(1,13)],
    "day":   [f"{d:02d}" for d in range(1,32)],
    "time":  ["12:00"],
    "area":  [37.5, 12.0, 35.5, 15.5],     # N, W, S, E
    "format": "netcdf",
}, "data/raw/era5_wind_2021_2023.nc")
```

```python
# 8.1b — CMEMS physics (salinity, currents, SSH, MLD) + waves + optics
# CONFIRM each dataset_id with: copernicusmarine describe --contains "MEDSEA_MULTIYEAR_PHY"
import copernicusmarine
BOX = dict(minimum_longitude=12.0, maximum_longitude=15.5,
           minimum_latitude=35.5,  maximum_latitude=37.5)
DATES = dict(start_datetime="2021-01-01T00:00:00",
             end_datetime="2023-12-31T00:00:00")

jobs = [
    # (dataset_id, variables, output_filename)
    ("cmems_mod_med_phy-sal_my_4.2km_P1D-m", ["so"],          "phy_sal.nc"),
    ("cmems_mod_med_phy-cur_my_4.2km_P1D-m", ["uo","vo"],     "phy_cur.nc"),
    ("cmems_mod_med_phy-ssh_my_4.2km_P1D-m", ["zos"],         "phy_ssh.nc"),
    ("cmems_mod_med_phy-mld_my_4.2km_P1D-m", ["mlotst"],      "phy_mld.nc"),
    ("cmems_mod_med_wav_my_4.2km_P1D-m",     ["VHM0","VTM02","VMDR"], "wav.nc"),
    ("cmems_obs-oc_med_bgc-transp_my_l3-multi-1km_P1D", ["KD490"], "kd490.nc"),
    ("cmems_obs-oc_med_bgc-optics_my_l3-multi-1km_P1D", ["PAR"],   "par.nc"),
]
for ds_id, vars_, fn in jobs:
    try:
        copernicusmarine.subset(dataset_id=ds_id, variables=vars_,
                                output_filename=fn, output_directory="data/raw",
                                **BOX, **DATES)
        print("OK:", fn)
    except Exception as e:
        print(f"FAILED {ds_id} — run `describe` to confirm the current id. {e}")
```

> **If a download fails**, it's almost always a drifted `dataset_id`. Run `copernicusmarine describe --contains "MEDSEA_MULTIYEAR_WAV"` (etc.), copy the exact short-name, and retry. Don't fight it — the family code is the stable anchor.

### 8.2 — Regridding: get everything onto one grid

You're mixing **~1 km** ocean colour, **~4 km** physics/waves, **~25 km** ASCAT and **~31 km** ERA5. The chl-a grid is the finest and is your **target grid** — regrid every predictor *onto it* (never downgrade the target).

```python
# 8.2 — regrid_predictors.py
import xarray as xr
chl = xr.open_dataset("data/raw/chl_malta_2021_2023.nc").CHL   # target grid

def to_chl_grid(da):
    # rename coords if needed, then bilinear interp onto chl lat/lon
    if "lat" in da.coords:  da = da.rename({"lat":"latitude","lon":"longitude"})
    return da.interp(latitude=chl.latitude, longitude=chl.longitude)
```

> **Conceptual caution:** interpolating a 31 km ERA5 field onto a 1 km grid does **not** create real 1 km wind detail — it just makes the arrays align. That's fine and expected; just don't over-interpret fine spatial structure in a coarse predictor. Coarse fields contribute *large-scale* signal (the AIS, basin-scale wind), which is exactly what you want from them.

### 8.3 — Derived wind features

```python
# 8.3 — wind derivatives (add to your feature builder)
import numpy as np
# wind speed & direction
feat["wind_speed"] = np.sqrt(u**2 + v**2)
# wind-stress curl (upwelling proxy) — finite differences on the grid
# Bakun upwelling index over 3- and 7-day windows (alongshore stress component)
# ... compute and add as feat["upwelling_idx_3d"], feat["upwelling_idx_7d"]
```

### 8.4 — Correlated-predictor handling (the part most people skip)

Your instinct — *use all, then feature importance* — is right, **but** raw per-feature importance lies when predictors are correlated: two collinear features (e.g. ERA5 wind and ASCAT wind, or SST and salinity and SSH that all co-vary with the AIS) **split** their shared importance, each looking weak, and you wrongly drop both. Fix it with three layers:

```python
# 8.4a — look at correlation BEFORE trusting importance
import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
df = pd.read_parquet("data/processed/supervised_sample.parquet")
corr = df[feature_cols].corr(method="spearman")
plt.figure(figsize=(12,10)); sns.heatmap(corr, center=0, cmap="RdBu_r")
plt.tight_layout(); plt.savefig("figs/feature_corr.png", dpi=150)
# Flag any pair with |corr| > 0.9 — candidates to merge or treat as one group
```

```python
# 8.4b — GROUPED permutation importance (read importance per theme, not per column)
from sklearn.inspection import permutation_importance
import numpy as np, xgboost as xgb

groups = {
    "chl_history": [c for c in feature_cols if c.startswith(("log_chl_lag","log_chl_roll","log_chl_t0"))],
    "gaps":        [c for c in feature_cols if c.startswith("gap_age")],
    "sst":         [c for c in feature_cols if c.startswith("sst_")],
    "wind":        [c for c in feature_cols if c.startswith(("wind_","upwelling_"))],
    "waves":       [c for c in feature_cols if c.startswith(("VHM0","VTM02","VMDR"))],
    "salinity":    [c for c in feature_cols if c == "so"],
    "currents_ssh":[c for c in feature_cols if c in ("uo","vo","zos","sla","adt","ugos","vgos")],
    "mld":         [c for c in feature_cols if c == "mlotst"],
    "optics":      [c for c in feature_cols if c in ("KD490","PAR")],
    "static_time": [c for c in feature_cols if c.startswith(("bathy","doy_"))],
}

model = xgb.XGBRegressor(); model.load_model("models/xgb_h1.json")
# permute each GROUP together and measure the val-score drop
# (sklearn permutes one column at a time; loop groups, permuting all cols in a group)
```

```python
# 8.4c — ABLATION by group: retrain without each group, watch val R²
# baseline = all groups. Then for each group g: drop g, retrain, record ΔR².
# A group that, when removed, barely changes val R² is not pulling weight —
# even if individual columns looked "important".
```

### ✅ Validation gate 8
- [ ] Correlation heatmap saved; you've **identified collinear pairs** (`|ρ| > 0.9`) and decided to merge/keep-one/group them
- [ ] Importance is read **by group** (permutation or summed-SHAP), not by raw single-column gain
- [ ] You ran a **group ablation** — each kept group measurably improves val R²; groups that don't are dropped
- [ ] **Regional check holds:** wind/upwelling help more in the **coastal/Adventure-Bank strip** than offshore, while **currents/SSH (AIS proxy)** dominate offshore (consistent with the literature: AIS advection ~78% of variance offshore, wind upwelling ~1.4%). If wind dominates *offshore*, suspect a bug.
- [ ] You did **not** include the BGC model's `chl` as a predictor (circularity)
- [ ] Final feature set, per-group importance, and per-horizon scores logged in one table

---

## Stage 9 — Bloom-event detection

**Goal:** layer bloom detection on top of forecasts. Implement the three definitions, pick one as headline.

- [ ] Build per-pixel daily **climatology** from the long record
- [ ] Label blooms via (a) median+5%, (b) percentile classes, (c) cumulative-sum
- [ ] Detect on **forecasted** CHL; score with POD / FAR / CSI / F1

```python
# 9.1 — bloom_labels.py  (median + 5% of annual median, after Siegel et al. 2002)
import xarray as xr, numpy as np
chl = np.log10(xr.open_dataset("data/raw/chl_malta_2021_2023.nc").CHL)

# per-pixel day-of-year climatological median (the seasonal expectation)
clim = chl.groupby("time.dayofyear").median("time")
annual_median = chl.median("time")
threshold = clim + np.log10(1.05)          # +5% in linear space ≈ +log10(1.05)

# bloom = observed exceeds its seasonal threshold
doy = chl.time.dt.dayofyear
thr_aligned = threshold.sel(dayofyear=doy)
bloom = (chl > thr_aligned)
print("Overall bloom-pixel fraction:", float(bloom.mean()))
```

```python
# 9.2 — score bloom detection on forecasts (binary skill scores)
def bloom_skill(obs_bloom, pred_bloom):
    tp = int(( obs_bloom &  pred_bloom).sum())
    fp = int((~obs_bloom &  pred_bloom).sum())
    fn = int(( obs_bloom & ~pred_bloom).sum())
    pod = tp/(tp+fn) if tp+fn else float("nan")          # detection rate
    far = fp/(tp+fp) if tp+fp else float("nan")          # false alarms
    csi = tp/(tp+fn+fp) if tp+fn+fp else float("nan")    # critical success
    f1  = 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else float("nan")
    return dict(POD=pod, FAR=far, CSI=csi, F1=f1, n_events=tp+fn)
```

### ✅ Validation gate 9
- [ ] Bloom-pixel fraction is **low** (single-digit to low-double-digit %) — this is an oligotrophic basin; a high fraction means your threshold is wrong
- [ ] You scored detection with **POD, FAR, CSI, F1** (not just accuracy — accuracy is misleading on rare events)
- [ ] **Decision branch:** if bloom-class **F1 < 0.5 across all three definitions**, fall back to **anomaly detection** (Isolation Forest on forecast residuals) as the headline result, per the research plan
- [ ] Detection skill **degrades with horizon** (good at H+1..H+3, weaker by H+5) — expected and worth reporting

---

## Stage 10 — Walk-forward validation (operational realism)

**Goal:** replace the single split with **expanding-window walk-forward** retraining — this is what a deployed system actually does, and reviewers will expect it.

- [ ] Implement quarterly expanding-window folds
- [ ] Report mean ± std of metrics across folds
- [ ] Compare to the single-split numbers (they should be in the same ballpark)

```python
# 10.1 — walk_forward.py (sketch)
import pandas as pd, numpy as np, xgboost as xgb
from sklearn.metrics import r2_score
df = pd.read_parquet("data/processed/supervised_sample.parquet").sort_values("time")
quarters = pd.period_range(df.time.min(), df.time.max(), freq="Q")

scores = []
for i in range(4, len(quarters)-1):                # need history before first test
    train_end = quarters[i].end_time
    test_q    = quarters[i+1]
    tr = df[df.time <= train_end]
    te = df[(df.time > test_q.start_time) & (df.time <= test_q.end_time)]
    # ... fit on tr, predict te for each horizon, append r2 to scores ...
print("Walk-forward mean R2 ± std reported here")
```

### ✅ Validation gate 10
- [ ] At least **6–8 walk-forward folds** completed
- [ ] Mean ± std reported per horizon; std is **not huge** (wildly varying folds suggest instability or too-small folds)
- [ ] Walk-forward mean R² is **consistent with** (usually slightly below) the single-split test R² — a big gap means the single split was lucky
- [ ] You can now state results as "R² = X ± Y across N quarterly folds" — publication-grade phrasing

---

## Stage 11 — Scale up & freeze results

**Goal:** rerun the validated pipeline on the **full record** (1998–present) and lock the final numbers.

- [ ] Re-download CHL + covariates for the full period (1998–2024)
- [ ] Rebuild dataset (reuse Stage 4 code unchanged — that's why we validated it)
- [ ] Rerun Stages 6, 9, 10 at full scale
- [ ] Archive: data version, code commit hash, model files, metric tables

### ✅ Validation gate 11 (final)
- [ ] Full-record results reproduce the small-scale trends (no nasty surprises)
- [ ] All figures regenerate from scripts with **one command** (reproducibility)
- [ ] Every number in your eventual paper traces to a saved script + data version
- [ ] `requirements.txt` / `environment.yml` frozen (`pip freeze > requirements.txt`)
- [ ] README documents: exact dataset IDs, date ranges, the coverage decision (Gate 2), and the L4→L3 delta (Gate 6)

---

## Learning checkpoints — concepts to be able to explain

By the end you should be able to explain, in your own words:

1. **Why L3 not L4?** — L4 is gap-filled by the data producer (DINEOF/OI); training ML on it conflates *your* skill with *their* interpolation. L3 keeps gaps honest.
2. **Why log10(CHL)?** — chlorophyll is log-normally distributed; errors are multiplicative; log space is the standard error space for ocean colour.
3. **Why native NaN handling matters** — XGBoost/LightGBM learn a default split direction for missing values, so gaps become *information* rather than something to fabricate.
4. **Why persistence is the baseline to beat** — at short horizons "tomorrow ≈ today" is shockingly strong; beating it is the real evidence of skill.
5. **Why chronological splitting is non-negotiable** — random shuffling leaks future into past and inflates every metric.
6. **Why the coverage atlas comes first** — it determines whether daily forecasting is even physically possible in winter.
7. **Why POD/FAR/CSI not accuracy for blooms** — rare-event detection makes accuracy meaningless (predict "no bloom" always → 90%+ accuracy, 0% usefulness).
8. **Why model fields are fine as predictors but not as the target** — scoring a model on reproducing an observed target while *feeding it* a modelled version of that target is circular; using modelled wind/salinity/currents as *inputs* is not, because they're never the thing being scored.
9. **Why correlated predictors mislead importance** — collinear features split their shared credit and each looks weak; you must read importance by *group* and confirm with *ablation*, not trust raw single-column gain.

---

## Quick-reference: the validation gates in one list

| Stage | The one check that matters most |
|---|---|
| 0 | Catalogue reachable, dataset ID resolves |
| 1 | CHL has NaNs (it's L3, not L4) + median ≈ 0.05–0.5 |
| 2 | Winter coverage ≥ 25%? (decides daily vs 3-day) |
| 3 | All cubes share lon/lat conventions |
| 4 | **Leakage assert passes** (targets vs lags aligned) |
| 5 | Persistence scores recorded per horizon |
| 6 | Beats persistence at H+3+; R² decays with horizon |
| 7 | Top features physically plausible |
| 8 | Importance read by **group** + confirmed by ablation; collinear pairs handled |
| 9 | Bloom fraction low; scored with POD/FAR/CSI/F1 |
| 10 | Walk-forward mean ≈ single-split (no lucky split) |
| 11 | One-command reproducibility; L4→L3 delta documented |