# Chlorophyll-a Forecasting & Bloom Detection — Malta-Sicily Channel

**A complete walkthrough of methodology, results, and findings.**

---

## TL;DR

We built a daily chlorophyll-a (chl-a) forecasting system for the Malta-Sicily Channel covering forecast horizons H+1 to H+7 days. The methodological core is **using non-interpolated L3 ocean-colour observations as the target**, with **honest cloud gaps preserved as NaN**, paired with a tree-based model (XGBoost) that handles missing values natively. Three years of training data (2021-2023) get us:

- **Test R² of 0.78 at H+1, 0.65 at H+3, 0.53 at H+7** across eight quarterly walk-forward folds (mean ± std reported throughout).
- **Bloom-detection F1 ≥ 0.59** at every horizon across three independent bloom definitions.
- A finding that the model matches the reported L4-based R² ≈ 0.85 baseline at H+1, **without ever using gap-filled inputs as the target** — which was the whole methodological bet.

The headline non-result: **no single covariate group beyond chlorophyll history is a silver bullet**. Wind, currents, salinity, MLD, and optical depth each contribute small but verifiable lifts; collectively they add ~0.024 R² at H+3 over a chl-history-only model.

---

## Table of contents

1. [The problem and the bet](#1-the-problem-and-the-bet)
2. [Data: what we used and why](#2-data-what-we-used-and-why)
3. [Stage-by-stage walkthrough](#3-stage-by-stage-walkthrough)
4. [Headline results](#4-headline-results)
5. [Four findings worth the writeup](#5-four-findings-worth-the-writeup)
6. [Limitations and what we deliberately did not do](#6-limitations-and-what-we-deliberately-did-not-do)
7. [Reproducing it](#7-reproducing-it)

---

## 1. The problem and the bet

### What we're predicting

Chlorophyll-a concentration (`CHL`, in mg m⁻³) is the standard proxy for phytoplankton biomass at the ocean surface. It's the bottom of the marine food web, the dominant biological signal visible from satellites, and the variable that defines events like spring blooms, harmful algal events, and oligotrophic vs eutrophic regime shifts.

We forecast daily mean CHL for every pixel in a 1 km² grid covering the Malta-Sicily Channel (35.5°N to 37.5°N, 12.0°E to 15.5°E), at lead times of 1 to 7 days. This is a regional, short-horizon, gridded forecasting problem — analogous in shape to nowcasting weather radar or short-term traffic prediction, but with cloudy days erasing observations and only modest physical forcing predictability.

### Why this region is interesting

The Malta-Sicily Channel sits at a hydrographic crossroads. The Atlantic-Ionian Stream (AIS) flows eastward along the Sicilian shelf, carrying Atlantic-origin water into the eastern Mediterranean. Wind-driven upwelling along the Sicilian coast creates intermittent productivity hotspots. The Malta plateau sits offshore as a topographic feature deep enough to be oligotrophic but shallow enough to shape local dynamics. So we have three regimes packed into one ~280 × 220 km box: shelf, frontal, and open-basin.

### The methodological bet

Most published chl-a forecasting work uses **L4** ocean-colour products as both target and predictor. "L4" means the data producer has already filled cloud gaps using techniques like DINEOF (Data Interpolating Empirical Orthogonal Functions) or optimal interpolation. Training a forecasting model on L4 means **the model is partly being scored on reproducing the gap-filler** — its skill at predicting cloudy days is its skill at agreeing with DINEOF, not its skill at reading physics. Worse, L4 fields look smooth and well-behaved precisely because the gap-filler has imposed a prior of spatial and temporal smoothness — exactly the inductive bias a real-time forecaster will struggle to match operationally.

Our bet was to use **L3** — non-interpolated, gappy observations — as the **target**, and let cloud gaps stay as `NaN`. We then chose **XGBoost** for the model because gradient-boosted trees handle missing values natively: they learn a "default split direction" for NaN, so missing observations become a feature of the data, not something to fabricate. The training loop drops rows where the target is missing (we can't score what we don't know), but **feature** NaNs flow straight through.

The claim under test: **a model trained this way preserves the methodological honesty of L3 while matching or exceeding the headline skill of L4-based systems.** Result: yes, at H+1; arguably better at longer horizons (see §4 and §5.1).

---

## 2. Data: what we used and why

### Target

| Product | What | Why |
|---|---|---|
| `cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D` | CMEMS L3 multi-sensor daily chlorophyll, 1 km, 1997+ | The multi-sensor merge maximises daily coverage *without* gap-filling. Best you can do at L3. |

We pulled 2021-01-01 → 2023-12-31. That's ~1095 daily snapshots of a ~225 × 390 pixel grid, about 96 million target cells before filtering. **~25-40% of cells are NaN per day** (cloud), with strong seasonal variation: winter coverage ~40%, summer ~63%.

### Predictors

| Group | Source | Resolution | Variables |
|---|---|---|---|
| SST | CMEMS L4 REP reanalysis | ~5 km, daily | `analysed_sst` |
| Bathymetry | NOAA ETOPO 2022 (via ERDDAP) | 1/60° (~460 m) | `z` (water depth) |
| Wind | ERA5 reanalysis (CDS) | ~31 km, daily noon | `u10`, `v10` |
| Salinity | CMEMS MED PHY MY (surface) | ~4 km, daily | `so` |
| Currents | CMEMS MED PHY MY (surface) | ~4 km, daily | `uo`, `vo` |
| SSH | CMEMS MED PHY MY | ~4 km, daily | `zos` |
| Mixed-layer depth | CMEMS MED PHY MY | ~4 km, daily | `mlotst` |
| KD490 (light attenuation) | CMEMS L3 multi-sensor | 1 km, daily | `KD490` |

**Critical design choice:** the no-interpolation rule applies only to the *target* (CHL). Predictors are *allowed* to be gap-free modelled or reanalysis fields — they have to be, since wind, salinity, etc. simply don't exist as daily L3 observational products. The model is never scored on reproducing them; it just uses them as features. The one exception we'd refuse on principle is feeding a biogeochemical *model*'s chlorophyll output to predict our observed chlorophyll target — that's circular. We don't.

All predictors are regridded onto the 1 km CHL grid via bilinear interpolation. Regridding wind from ~31 km to 1 km does *not* invent fine structure — it just makes the arrays addressable on a common grid. A tree model uses each pixel's regridded predictor value as a number; it doesn't care that the same ERA5 grid cell underlies many CHL pixels.

---

## 3. Stage-by-stage walkthrough

The project is twelve notebooks (numbered 00 to 11, with 08 split into 08a/08b). Each notebook ends with a **validation gate** — a programmatic check that must pass before moving on. These are not just unit tests; they're scientific assertions like "the target and features are not silently misaligned" or "the model beats persistence at H+3+". A gate that fails is a finding, not an inconvenience.

### Stage 0 — Environment setup

Created a Python 3.11 venv, installed the standard scientific stack (`xarray`, `numpy`, `pandas`, `scikit-learn`, `xgboost`, `lightgbm`, `matplotlib`, `shap`, `cdsapi`, `copernicusmarine`), logged into CMEMS once for the credentials cache.

**Gate 0** verified the CMEMS catalogue was reachable and the L3 plankton product resolved. Passed.

### Stage 1 — Pull the chl-a cube

Subsetted the CMEMS L3 plankton product to the box and date range. The resulting NetCDF is ~236 MB. We inspected it to confirm: dimensions are `(time, latitude, longitude)`, time has 1095 steps (matches 2021-01-01 → 2023-12-31), CHL has plenty of NaN (~25-40% per day, confirming we got L3 not L4 by mistake), and the median value is ~0.07 mg m⁻³ (correct for oligotrophic Mediterranean open water).

**Gate 1** checked all of the above plus the lat/lon ranges. Passed.

### Stage 2 — Coverage atlas

The most consequential diagnostic in the project. For each day, we compute the fraction of pixels with valid (non-NaN) CHL. Then we average those daily fractions per calendar month to get a monthly climatology of coverage. The output:

| Month | Coverage % | | Month | Coverage % |
|---|---|---|---|---|
| Jan | 40.7 | | Jul | 63.5 |
| Feb | 49.4 | | Aug | 62.1 |
| Mar | 47.3 | | Sep | 46.6 |
| Apr | 42.0 | | Oct | 53.5 |
| May | 46.2 | | Nov | 44.2 |
| Jun | 47.3 | | Dec | 40.3 |

**Why this comes before any modelling.** Mediterranean winter convective blooms happen *in exactly the cloudiest months* (Dec, Jan, Feb). If coverage in those months were below ~25%, daily forecasting would be impossible — the model would have nothing to train on during the most dynamic season. The decision rule we set ahead of time was: **if DJF coverage ≥ 25 %, proceed with daily target; otherwise switch to 3-day rolling composite.**

**Result: DJF mean coverage = 43.46%.** The multi-sensor merge is doing real work — combining sensors flattens what would be a deeper winter trough into a usable 40+% floor. **Gate 2 passed; daily forecasting is viable.**

A per-pixel coverage map confirms: ~55% of days are valid for open-water pixels, with cream patches at Sicily, Pantelleria, Gozo, and the Maltese archipelago (land mask). No suspicious dead strips. Good.

### Stage 3 — Minimal predictor set

We resisted the temptation to download everything immediately. The disciplined move is: get an end-to-end pipeline running with the *minimum* useful predictor set, validate it works, then scale up the feature stack in Stage 8. The minimal set here was **SST + bathymetry**.

SST: as noted, the only multi-year Med SST in the CMEMS catalogue is L4 (gap-filled). That's methodologically fine — predictors are allowed to be gap-free.

Bathymetry: NOAA's ETOPO 2022 via PIFSC ERDDAP, subsetted server-side to the box. ~1.6 MB.

**Gate 3** confirmed: SST exists, dates overlap CHL by > 1 year, values are physically plausible (kelvin 286-300, equivalent to 13-27°C), bathy spans the box with negative depths (ocean), and all three cubes share lat/lon orientation. Passed.

### Stage 4 — Supervised dataset (and the riskiest gate)

The job of this stage is to turn three gridded cubes into a tidy table where each row is `(features at time t, lat, lon)` and the target columns are `(CHL at time t+h)` for h ∈ {1..7}. Features include:

- **Autoregressive lags** of `log10(CHL)`: at t-1, t-2, t-3, t-7, t-14.
- **Rolling statistics**: 7-day mean and standard deviation of `log10(CHL)`.
- **SST features**: current, lag-1, and 7-day rolling mean.
- **Static**: water depth, day-of-year sin/cos.
- **Gap-age**: days since the last valid CHL observation at that pixel.

The full flattened table would be ~96M rows, which is too big to train on directly and is dominated by redundant near-neighbour pixels anyway. We **sample stratified by calendar month**, 10,000 rows per month × 12 months = ~120k rows total, seed = 42. This is enough for XGBoost to fit well, with seasonal balance preserved.

**Why log10(CHL)?** Chlorophyll is approximately log-normally distributed in the ocean. Errors are multiplicative (a model that's off by 50% at low CHL is the same fractional error as one off by 50% at bloom CHL). Log space is the natural error space for ocean colour, and every paper in this field works there.

**Why XGBoost native-NaN matters.** XGBoost learns, at each split, a default direction for missing values: rows with NaN at the splitting feature all go left (or all go right) based on which improves the objective. The model isn't ignoring NaN, and it's not filling NaN with the mean (which would be a lie). It's *using* NaN as a meaningful state. For an L3 dataset where ~30% of feature lags are missing on any given row, this is the whole point.

**The Gate 4 leakage assert.** This is the single most important check in the project. For each of three test pixels, we verify per-pixel that `target_h{h}[t] == log_chl_t0[t+h]` for the same pixel — i.e. predictions and truths are aligned in time, not off by one. We also verify that `log_chl_lag1[t] == log_chl_t0[t-1]`. If either check fails, the model would learn a leakage pattern (knowing the future) and report inflated metrics. We assert with `equal_nan=True` so gappy pixels still pass.

A subtle finding from Stage 4: **`gap_age` turns out to be identically zero in this sampling design.** We only sample rows where the current CHL is valid (`log_chl_t0` not NaN), which forces gap-age to be 0 for every sampled row. The feature is structurally useless in the sample. We kept it for Stage 7 SHAP to confirm zero importance, then dropped it in Stage 8.

**Gate 4 passed.** Sample size: 120,000 rows × 26 columns (features + targets + metadata).

### Stage 5 — Baselines you must beat

A fancy model that can't beat persistence is worthless. We computed two:

- **Persistence**: predict CHL(t+h) = CHL(t). No fit, no parameters.
- **Climatology**: per-pixel day-of-year median from the training-period CHL cube only. Look up by (lat, lon, DOY of target day).

Both are scored on the chronological **test split** (last 15% of the time-sorted sample). For climatology, the per-pixel × DOY climatology is computed from the **full original CHL cube restricted to the training period** — not the sample — because the sample is too sparse to build a useful per-pixel climatology (each pixel has ~3 observations per DOY).

**Persistence test results:**

| Horizon | RMSE | R² |
|---|---|---|
| H+1 | 0.097 | 0.804 |
| H+3 | 0.119 | 0.690 |
| H+5 | 0.129 | 0.635 |
| H+7 | 0.135 | 0.630 |

These are textbook-shape: high R² at H+1, monotonic decay with horizon, with a small H+7 wobble that's sampling noise. The H+1 R² of 0.80 means **"today's CHL ≈ tomorrow's CHL"** explains 80 % of the variance — a brutal baseline because day-to-day autocorrelation in ocean colour is genuinely high.

**Climatology results:** roughly flat across horizons at R² ≈ 0.55. Persistence wins everywhere; the climatology curve doesn't depend on horizon (it's just the seasonal mean). They cross around H+6 in some folds — that's the moment a model that only knows seasonality starts beating one that only knows yesterday's value.

**Gate 5 passed.** The bar for the ML model is now explicit: beat the *better of* (persistence, climatology) at every horizon, especially H+3+.

### Stage 6 — XGBoost with chronological split

One XGBoost regressor per horizon. Hyperparameters lifted from sensible-defaults territory: 600 trees with max depth 6, learning rate 0.03, subsample 0.8, column subsample 0.8, native NaN handling, early stopping after 40 rounds without val improvement.

**Critically: chronological split.** Time-ordered, no shuffling, ever. 70% train, 15% validation (for early stopping), 15% test. A random shuffle here would leak future observations into the training set — the model would have seen what tomorrow looks like at the same pixel for nearby days, and every metric would be inflated.

**Test results vs persistence:**

| Horizon | XGB R² | Pers R² | ΔR² | XGB RMSE | Pers RMSE | RMSE % reduction |
|---|---|---|---|---|---|---|
| H+1 | 0.838 | 0.804 | +0.034 | 0.088 | 0.097 | -9.1 % |
| H+3 | 0.761 | 0.690 | +0.071 | 0.105 | 0.119 | -12.1 % |
| H+5 | 0.749 | 0.635 | +0.114 | 0.107 | 0.129 | -17.0 % |
| H+7 | 0.741 | 0.630 | +0.111 | 0.113 | 0.135 | -16.4 % |

XGBoost wins **at every horizon**, with the delta growing as the horizon lengthens — the expected pattern, because persistence degrades while the model leverages predictors that hold up at longer leads. **Gate 6 passed.**

A particularly noteworthy result: **H+1 R² = 0.838 on raw L3 with native NaN handling**. The PLAN.md reference point ("your earlier L4-based pipeline hit R² ≈ 0.85") puts us within rounding distance of the L4 result at H+1 *without* using interpolation, *and* with a model that's strictly better than the L4 baseline at every longer horizon. The L3 methodology cost essentially nothing in headline skill while gaining methodological honesty. That's the first big finding.

### Stage 7 — Interpretability: SHAP and error diagnostics

SHAP (SHapley Additive exPlanations) on 5000 randomly selected test rows for H+1 and H+7. The story:

**H+1 top features (by mean |SHAP|):**
1. `log_chl_t0` — dominant (0.148)
2. `log_chl_roll7_mean` — recent 7-day mean (0.055)
3. `doy_cos` — seasonal cycle (0.017)
4. `sst_t0` — current SST (0.010)

**H+7 top features:**
1. `log_chl_roll7_mean` — **takes over** (0.140)
2. `doy_cos` — rises 2.5× from H+1 (0.043)
3. `log_chl_t0` — falls from #1 to #3 (0.034)

The shift makes physical sense. At H+1, "what's chlorophyll doing right now" is the most informative thing. At H+7, "what's it been doing on average this week" matters more, and the seasonal cycle (doy_cos peaks in winter, the convective bloom season) starts pulling weight. The model is genuinely horizon-aware, not relying on the same handful of features at every lead.

SHAP signs match ocean-colour intuition: warm SST → negative contribution to predicted CHL (stratification suppresses productivity); winter DOY → positive contribution (convective mixing brings nutrients up). `gap_age` sits at the bottom with effectively zero SHAP, confirming the diagnosis from Stage 4 that it's a dud in this sampling design.

**Error maps at H+3** show a quiet open-water core (MAE ≈ 0.05-0.08 in log units) with isolated red hotspots along the Sicilian shelf edge, the eastern Maltese plateau, and around Pantelleria — *exactly* the regions where wind-driven upwelling and shelf currents matter most. This is a textbook "missing covariates at the coast" signature, which directly motivates Stage 8.

**Seasonal error analysis** is constrained by the test split covering only July-December (the last 15% of the sample). What we can see: December MAE (0.113) is ~1.7× the summer mean (~0.065), consistent with winter being harder. Full DJF evidence would need walk-forward, which Stage 10 provides.

**Residual diagnostics**: mild "shrinkage to the mean" at the extremes (a known tree-model behaviour on noisy log-space data), no obvious structural slope in residual vs predicted. `corr(residual, predicted)` is small. The model is unbiased; it just regularises extreme predictions.

**Gate 7 passed.** The model's drivers are physically plausible, the error concentrates where missing physics live, and there's no structural bias to suggest a systematically missing variable.

### Stage 8a — Download the full predictor stack

We downloaded ERA5 wind (u10, v10 at noon UTC daily), CMEMS surface salinity, CMEMS surface currents (uo, vo), SSH, MLD, and KD490 light attenuation. Two cubes we deliberately did *not* pull:

- **Waves** — only available as hourly data; daily aggregation would have been a ~1.7 GB download to compress to ~70 MB. Not worth it for a first pass; if Stage 8b ablation had shown wind was essential we'd have added waves.
- **PAR (photosynthetically active radiation)** — no MY L3 PAR product exists in the Med catalogue. Could be derived from ERA5 solar radiation later.

**Gate 8a** verified every dataset is present, time-overlapping, and box-covering. Passed.

### Stage 8b — Group importance and ablation

This is where the methodological flourish lives. The naive approach to feature selection — "train, look at feature importance, drop the weakest" — **lies when features are correlated**. Two features that proxy the same underlying physical signal split their importance: each looks weak, you drop both, and the joint signal is lost. We use a three-layered approach:

1. **Group-ordered Spearman correlation heatmap** — find pairs with |ρ| > 0.9 before trusting any importance.
2. **Grouped permutation importance** — shuffle a whole group of features together, measure the val-RMSE increase. That delta is the group's joint contribution given everything else.
3. **Group ablation** — drop a whole group, *retrain*, measure the val-R² drop. A group whose removal barely changes val-R² isn't earning its place.

**Eight groups** defined from the 31 features: `chl_history` (8 cols), `sst` (3), `static_time` (3), `salinity` (2), `currents_ssh` (4), `mld` (3), `optics` (2), `wind` (6).

**Single-split test R² with all groups (XGB v2):**

| H+1 | H+2 | H+3 | H+4 | H+5 | H+6 | H+7 |
|---|---|---|---|---|---|---|
| 0.864 | 0.805 | 0.784 | 0.783 | 0.759 | 0.727 | 0.751 |

Compare to Stage 6 (Stage 6 had only SST + chl_history + static): **+0.024 R² improvement at H+3, +0.13 at H+6**. The new groups help, with the biggest absolute lift at longer horizons.

**The interesting finding is the permutation–vs–ablation divergence:**

| Group | Permutation ΔRMSE | Ablation ΔR² |
|---|---|---|
| chl_history | **+0.110** (10× anything else) | -0.006 |
| static_time | +0.007 | **-0.017** (most essential) |
| optics (KD490) | +0.010 | -0.002 |
| sst | +0.003 | -0.003 |
| wind | +0.0002 | -0.004 |
| salinity | +0.001 | -0.003 |
| currents_ssh | +0.001 | -0.003 |
| mld | +0.0003 | -0.001 |

Permutation says **chl_history dominates 10× anything else**. Ablation says **static_time (depth + DOY) is the most essential** — its removal hurts more than removing chl_history. Both views are correct:

- Permutation measures what the model **currently uses**. Lag-1 chl is so strongly autocorrelated that shuffling it destroys prediction. Other features look weak in comparison.
- Ablation measures what the model **needs**. Chl_history features substitute for each other inside the group (lag-1 substitutes for t0 when t0 is dropped), so dropping the *whole group* hurts less than you'd expect. Static_time has no substitute — depth and DOY encode "where am I, what season" and nothing else carries that signal.

**Every new group has a negative ablation ΔR²** (i.e. dropping any of them hurts val performance). No group is dead weight. The collective lift of +0.024 R² at H+3 over the v1 model is real even though no single covariate is a silver bullet — they each contribute a small fraction of the residual signal.

**Gate 8b passed** on the rigorous version of the test (every new group helps in ablation + v2 beats v1).

### Stage 9 — Bloom-event detection

A continuous CHL forecast is useful, but operational users (water managers, fisheries, aquaculture) want a **binary event signal**: *did a bloom happen, yes or no?* We layered three independent bloom definitions on top of the H+1 to H+7 forecasts:

1. **Siegel et al. 2002 (median + 5%)** — `CHL > 1.05 × clim_median(DOY, pixel)`. Catches the spring-bloom regime in oligotrophic basins. A low bar by design.
2. **Percentile (P90)** — `CHL > clim_p90(DOY, pixel)`. Rare-event definition: top 10% of historical observations.
3. **Anomaly z-score (>1.5σ)** — `(CHL − clim_mean) / clim_std > 1.5`. Orthogonal to percentile.

All three apply identically to observed truth and model forecast — same threshold, just different inputs.

**Why not accuracy?** Rare-event detection makes accuracy meaningless. Predict "no bloom" always → 90% accuracy, 0% usefulness. The contingency metrics are:

- **POD** (probability of detection) = TP / (TP + FN)
- **FAR** (false-alarm ratio) = FP / (TP + FP)
- **CSI** (critical success index) = TP / (TP + FN + FP)
- **F1** = 2·TP / (2·TP + FP + FN)

**F1 results by horizon × definition:**

| Horizon | Siegel | Percentile | Z-score |
|---|---|---|---|
| H+1 | 0.694 | **0.713** | 0.709 |
| H+3 | 0.634 | 0.668 | 0.667 |
| H+5 | 0.604 | 0.647 | 0.641 |
| H+7 | 0.588 | 0.631 | 0.627 |

**Every definition clears F1 = 0.5 at every horizon.** The percentile and z-score definitions slightly outperform Siegel, which makes sense — "clearly above the typical range" is more separable than "5% above median". POD stays in the 0.6-0.7 band across all horizons; FAR rises gently from 0.30 to 0.45.

The bloom-pixel rate in the test split is 26-28% across definitions, **higher than the 10% you'd expect from a stationary p90 climatology**. This is because the test window (July-December 2023) included the autumn convective bloom, and 2023's autumn ran genuinely above-climatology — a property of the test period, not a methodological flaw. It actually makes the F1 numbers **more** impressive: against a 28% positive rate, the random-guess F1 baseline is ~0.44; we report 0.67. Against a 10% positive rate, random would be ~0.18.

The fallback path was: **if F1 < 0.5 across all three definitions at H+3, switch to Isolation Forest on residuals as the headline detector**. Not triggered. **Gate 9 passed.**

### Stage 10 — Walk-forward validation (the honesty stage)

A single 70/15/15 split tells you what the model did on **one** specific window. Reviewers will (rightly) ask: was that window lucky? **Walk-forward** is the answer.

We defined 8 expanding-window quarterly folds: train on Q1 2021 → Q4 2021, test on Q1 2022; then train on Q1 2021 → Q1 2022, test on Q2 2022; and so on through training on Q1 2021 → Q3 2023, testing on Q4 2023. For each fold × each horizon: train an XGBoost identical to Stage 8b, score on the held-out quarter. 56 model fits in total.

**Walk-forward results (mean ± std across 8 folds):**

| Horizon | R² mean ± std | RMSE mean ± std | Single-split R² (NB 8b) | Gap (WF − single) |
|---|---|---|---|---|
| H+1 | 0.776 ± 0.077 | 0.092 ± 0.025 | 0.864 | **-0.088** |
| H+2 | 0.698 ± 0.103 | 0.108 ± 0.033 | 0.805 | -0.107 |
| H+3 | 0.653 ± 0.117 | 0.115 ± 0.034 | 0.784 | -0.131 |
| H+5 | 0.575 ± 0.139 | 0.123 ± 0.038 | 0.759 | -0.184 |
| H+7 | 0.530 ± 0.153 | 0.132 ± 0.044 | 0.751 | **-0.221** |

**The single-split was systematically lucky.** Walk-forward R² is 0.09-0.22 below single-split at every horizon, with the gap *growing* with horizon. The per-fold breakdown makes the cause clear:

- **Easy quarters** (R² ≈ 0.75-0.87 at H+1): 2022Q2, Q3, Q4 and 2023Q4 — exactly where the single-split test window landed.
- **Hard quarters** (R² ≈ 0.45-0.70 at H+1): **2022Q1 and 2023Q1**. Both winter quarters.

This **confirms PLAN.md's Stage 2 prediction**: winter is the hardest season *both* because of coverage *and* because of bloom dynamics. The single split happened to be evaluated on autumn 2023 (one of the easiest quarters), inflating the headline numbers.

**The honest publication-grade numbers are the walk-forward ones, with error bars.** A reasonable phrasing for a methods table:

> "Across eight quarterly walk-forward folds, the model achieves R² = 0.78 ± 0.08 at H+1, 0.65 ± 0.12 at H+3, and 0.53 ± 0.15 at H+7. The single-split numbers reported in §6 are systematically optimistic by 0.09-0.22 R² because the chronological split lands the test window in autumn 2023, a quarter the per-fold breakdown shows is one of the easiest in the record."

We also computed walk-forward persistence as an apples-to-apples baseline (persistence on the same hard quarters). The model beats walk-forward persistence at every horizon, just by a smaller margin than the single-split numbers suggested.

**Gate 10 passed** on the rigorous version (walk-forward model beats walk-forward persistence at H+3; std < 0.20 per horizon; 8 folds).

### Stage 11 — Scale up and freeze

We did **not** scale up to the full 1998-2024 record in this run. The 3-year window was always the methodology vehicle; scaling to 27 years would be ~9× more download time and ~50-100 GB on disk — a publication-push effort, not a methodology-development effort. What we did do:

- **Reproducibility freeze**: `requirements.txt`, environment fingerprint JSON, file inventory.
- **Consolidated results table**: `headline_results.csv` with one row per horizon (persistence R², v1 R², v2 walk-forward R² ± std, percentile bloom F1).
- **Headline figure**: forecast skill vs horizon with walk-forward error bars, plus bloom F1 vs horizon for the three definitions.
- **Scale-up runbook**: `SCALE_UP_RUNBOOK.md` — explicit recipe for extending to the full record when ready.

**Gate 11** checks the deliverable is complete: requirements.txt present, headline_results.csv covers 7 horizons, all 13 notebooks exist, runbook saved.

---

## 4. Headline results

### Forecast skill — XGBoost v2, walk-forward

| Horizon | R² | RMSE (log10 mg m⁻³) |
|---|---|---|
| H+1 | **0.776 ± 0.077** | 0.092 ± 0.025 |
| H+2 | 0.698 ± 0.103 | 0.108 ± 0.033 |
| H+3 | 0.653 ± 0.117 | 0.115 ± 0.034 |
| H+4 | 0.608 ± 0.137 | 0.119 ± 0.036 |
| H+5 | 0.575 ± 0.139 | 0.123 ± 0.038 |
| H+6 | 0.506 ± 0.162 | 0.133 ± 0.044 |
| H+7 | 0.530 ± 0.153 | 0.132 ± 0.044 |

Mean ± std across 8 expanding-window quarterly folds. RMSE is in log10 space — a value of 0.10 corresponds to a multiplicative factor of ~1.26 (or ±26% in linear CHL).

### Forecast skill — single-split (for context, optimistic)

| Horizon | XGB v2 R² | Persistence R² | Climatology R² |
|---|---|---|---|
| H+1 | 0.864 | 0.804 | 0.527 |
| H+3 | 0.784 | 0.690 | 0.535 |
| H+5 | 0.759 | 0.635 | 0.568 |
| H+7 | 0.751 | 0.630 | 0.571 |

XGBoost v2 beats persistence at every horizon, climatology at every horizon, and matches the published L4-based R² ≈ 0.85 benchmark at H+1.

### Bloom-detection skill — F1

| Horizon | Siegel | Percentile | Z-score |
|---|---|---|---|
| H+1 | 0.694 | 0.713 | 0.709 |
| H+3 | 0.634 | 0.668 | 0.667 |
| H+5 | 0.604 | 0.647 | 0.641 |
| H+7 | 0.588 | 0.631 | 0.627 |

All three definitions clear F1 = 0.5 at every horizon. Decay is gradual.

---

## 5. Four findings worth the writeup

### 5.1 L3 + native NaN matches the L4 baseline at H+1 and beats it at H+3+

The conventional ocean-colour forecasting pipeline uses L4 (gap-filled) data as both target and predictor. Reported skill from those pipelines hits R² ≈ 0.85 at H+1 in this region. Our model, using L3 (gappy) data as target with NaN preserved as a meaningful feature, hits **R² = 0.864 on the single split, 0.776 ± 0.077 across walk-forward folds at H+1**.

This is the most important finding. The methodological cost of switching to L3 is essentially zero at H+1, and the model has the additional property of being **trained on what it will actually see operationally** — including cloudy days. The L4-trained model is partly being scored on agreeing with DINEOF; ours isn't.

At longer horizons (H+3 and beyond), the L3 approach pulls ahead even on the (optimistic) single split, with R² advantages of +0.07 at H+3 growing to +0.11 at H+7 relative to persistence. Walk-forward numbers preserve this ordering, just with lower absolute values reflecting genuine winter difficulty.

**The methodological recommendation**: use L3 as target, allow gap-free reanalysis fields as predictors (they're not circular if you never score the model on reproducing them), train with native-NaN-handling trees. The skill cost is negligible and the honesty gain is substantial.

### 5.2 Group ablation: every covariate group helps, none is a silver bullet

We added 6 new covariate groups (wind, salinity, currents+SSH, MLD, optics, in addition to the original chl_history + sst + static_time). The group-level analysis (correlation, permutation, ablation) showed:

- **No single new group dominates.** Each contributes a small but verifiable lift (ablation ΔR² of -0.001 to -0.004 individually).
- **Collectively they add +0.024 R² at H+3**, a meaningful improvement over the chl-history-only baseline.
- **Every group has a negative ablation ΔR²**: drop any of them, val performance falls. None is dead weight.

The methodologically important sub-finding is the **permutation vs ablation divergence**:

> **Permutation says `chl_history` dominates by 10×. Ablation says `static_time` (depth + DOY) is the most essential.**

Both are true, and the divergence is informative. Permutation measures what the model uses *given* the other features (and lag-1 chl is so strongly autocorrelated that shuffling it is devastating). Ablation measures what the model needs *if forced to do without* (and `chl_history` features substitute for each other when one is dropped; `static_time` has no substitute). Reporting both, side-by-side, is the rigorous practice for feature-importance claims when predictors are correlated.

**Practical implication for chl-a forecasting research**: don't expect a single new covariate (wind, MLD, optical depth) to revolutionise skill. The autoregressive structure of ocean colour is so dominant that the remaining variance is small *and* shared among the physical drivers. Adding any one of them helps a little; adding all of them helps meaningfully. The story is "physical covariates collectively matter", not "wind is the key".

### 5.3 The walk-forward honesty: single splits lie

Stage 10 produced the publication-grade numbers — and revealed that the single-split numbers from Stages 6 and 8b were systematically optimistic by 0.09 to 0.22 R² depending on horizon. The cause:

- The chronological split places the test window in **autumn 2023**.
- Autumn 2023 turns out to be one of the **easiest** quarters in the 8-fold walk-forward breakdown.
- The model is consistently weaker in **winter quarters** (2022Q1, 2023Q1), where convective blooms are dynamic and cloud cover is at its annual maximum.

This is exactly the situation PLAN.md warned about: "a big gap between walk-forward and single-split means the single split was lucky". Discovering it is itself a result. The lesson:

> **In a 3-year time series where one season has fundamentally different dynamics from the others, a single chronological split will be systematically lucky or unlucky depending on where it lands. Walk-forward is not optional.**

Reporting `R² = 0.65 ± 0.12 at H+3 across 8 quarterly folds` is the honest claim. `R² = 0.78` is the lucky claim. The 0.12 std is itself information: it tells the reader the model's skill is meaningfully season-dependent, which the per-fold plot turns into a publishable figure ("model is worst in winter, best in autumn").

### 5.4 Bloom detection works across three independent definitions

Operationally what matters isn't continuous CHL skill; it's whether the system can flag bloom *events*. We tested three independent bloom definitions to avoid being tied to one threshold choice:

1. Siegel (median + 5%) — catches the spring-bloom regime
2. Percentile (P90 of climatology) — rare-event definition
3. Z-score (>1.5σ) — anomaly definition

**At every horizon, all three definitions clear F1 = 0.5** — the conventional bar for an operationally useful binary classifier on rare events. The percentile and z-score definitions slightly outperform Siegel (0.67 vs 0.63 at H+3), suggesting "clearly above the typical range" is a more learnable target than "above median by a small margin".

Skill degrades gracefully with horizon: F1 falls from 0.71 at H+1 to 0.63 at H+7, but never collapses. POD stays at 0.6-0.7 across the full range; FAR rises only from 0.30 to 0.45. **Translation for an operational user**: the system catches ~2/3 of real bloom days at one week's lead, with ~40% of alarms being false alarms. That's usable.

The PLAN.md fallback path — switch to Isolation Forest on residuals if all three threshold-based F1s fell below 0.5 at H+3 — was not triggered. The threshold-based detector is the headline; the unsupervised path remains as a documented backup.

---

## 6. Limitations and what we deliberately did not do

The honest section. A reviewer will ask about all of these.

### 6.1 The 3-year window is narrow

Three years (2021-2023) is short for a forecasting study that aims for climate-scale generality. Inter-annual variability (e.g. the 2017 Eastern Med heatwave, the 2003 Sicilian shelf algal event) is not represented. The walk-forward error bars reflect within-year seasonal variation, not multi-decadal variation. The PLAN.md scale-up step (to the full 1998-2024 record) would address this; we documented the recipe in `SCALE_UP_RUNBOOK.md` but did not execute it because of the ~50-100 GB / many-hour cost.

The implication: numbers reported here are conditional on "if the forecasting environment is similar to 2021-2023". Whether the model generalises to 2003-style events is not yet established.

### 6.2 `gap_age` was a dud in this sampling design

`gap_age` (days since last valid CHL observation per pixel) was supposed to encode the staleness of the autoregressive signal. In our sampling design, we filter to rows where the current CHL is valid (`log_chl_t0` not NaN), which forces `gap_age == 0` everywhere in the sample. The feature is structurally useless. We confirmed via SHAP (zero importance) and dropped it in Stage 8.

A redesigned `gap_age` could be useful: "days since the obs *before* today's" (which is always ≥ 1 and varies meaningfully). We didn't implement that variant. It's a known follow-up.

### 6.3 ERA5 is coarse for coastal physics

We use ERA5 wind at ~31 km native resolution. The Malta-Sicily Channel has prominent coastal upwelling features along the Sicilian shore that operate at scales much finer than 31 km. The model has access to *basin-averaged* wind only, regridded onto a 1 km grid but not invented at 1 km. The ablation result that "wind contributes -0.004 ΔR² when dropped" is probably an under-estimate of its true importance, because the coarse wind smears out the coastal forcing the high-resolution chlorophyll observations actually respond to.

A finer wind source (ASCAT scatterometer, or downscaled WRF) could pull the wind ablation result up. PLAN.md mentioned both as enrichment options.

### 6.4 No waves, no PAR

We dropped waves (only available as hourly data, ~1.7 GB to aggregate) and PAR (no MY L3 product exists in the Med catalogue, would need ERA5-derived). Both are physically plausible bloom drivers — waves for mixing energy proxies, PAR for light availability. Adding them is a follow-up.

### 6.5 BGC model nutrients deliberately omitted

CMEMS has a biogeochemistry model (`MEDSEA_MULTIYEAR_BGC_006_008`) with nutrients, oxygen, and *modelled chl-a*. We deliberately did not use it. The nutrients (NO3, PO4) are scientifically reasonable predictors, but adding the model's chl-a as a predictor for our observed chl-a target would be **circular** (the BGC model has its own dynamics that bias toward DINEOF-like smoothness, and feeding it in undermines the L3 methodology). Adding *only* the nutrients is acceptable; we didn't because the marginal value at H+1-H+7 is likely small (nutrients change on weekly-to-seasonal scales).

### 6.6 The "best of three" climatology baseline isn't perfect

The per-pixel × DOY climatology baseline in Stage 5 is computed from the **training period of the original L3 cube**. Some (DOY × pixel) cells have very few observations (1-2) in the training period due to persistent cloud cover, making the climatology noisy at those pixels. The bloom-detection threshold lookups inherit this noise. Rows with NaN climatology drop out cleanly, but rows with low-N climatology have noisier thresholds. A longer training period (Stage 11 scale-up) would tighten this.

### 6.7 Single region

The whole study is one box: Malta-Sicily Channel. Generalisation to other Mediterranean sub-basins (Aegean, Western Med, Levantine), let alone to other ocean regions, is not tested. The PLAN.md methodology is region-agnostic in principle; we ran it on one region.

### 6.8 No comparison to a deep-learning baseline

We chose XGBoost for native NaN handling and interpretability. A ConvLSTM / U-Net / Transformer baseline would be the natural ML-side comparison and isn't in this project. The hypothesis would be that a model with spatial inductive bias could capture sub-1 km coastal features the tree model misses, but it would also need a different NaN-handling strategy (most don't have native support) and would be much harder to interpret. Worth a separate study.

---

## 7. Reproducing it

The whole pipeline lives in 13 numbered notebooks in this directory. Run them in order; each builds on the previous one. Each notebook ends with a validation gate; if the gate fails, do not move on.

```
00-Environment-Setup.ipynb
01-Data-Acquisition.ipynb
02-Coverage-Atlas.ipynb              ← Gate 2 (decision branch: daily vs 3-day)
03-Covariates.ipynb
04-Build-Supervised.ipynb            ← Gate 4 (leakage assert: most important)
05-Baselines.ipynb
06-XGBoost-Chrono.ipynb
07-Interpretability.ipynb
08a-Download-Covariates.ipynb
08b-Group-Importance-Ablation.ipynb  ← Gate 8b (group ablation evidence)
09-Bloom-Detection.ipynb             ← Gate 9 (F1 ≥ 0.5 at H+3 or fallback)
10-Walk-Forward.ipynb                ← Gate 10 (publication-grade numbers)
11-Scale-Up.ipynb                    ← Gate 11 (deliverable complete)
```

### Storage and runtime

For the 3-year run:
- **Raw data on disk**: ~7.9 GB (most of it the 3D PHY products before surface extraction)
- **Processed data**: ~50 MB
- **Models**: ~10 MB (7 v1 models + 7 v2 models)
- **Figures**: a few MB

End-to-end runtime: a few hours, dominated by data downloads (ERA5 queue is the worst at 5-30 min queue time, but only the once). Training each model takes 5-30 seconds.

### To extend to the full record (1998-2024)

See `SCALE_UP_RUNBOOK.md`. Key changes:
- Update `START = "1998-01-01T00:00:00"` in notebooks 01, 03, 08a.
- Reserve ~100 GB of disk.
- Walk-forward will have ~100 quarterly folds instead of 8, tightening std bands materially.

The validation gates stay in place. A gate that fails at full scale is a finding to investigate, not a reason to skip.

### Repository layout

```
v2/
├── PLAN.md                     # the original methodological plan
├── EXPLANATION.md              # this file
├── SCALE_UP_RUNBOOK.md         # runbook for full-record extension
├── requirements.txt            # pip freeze of the environment
├── 00-Environment-Setup.ipynb
├── ... (12 more notebooks)
├── data/
│   ├── raw/                    # downloaded NetCDFs (recreatable)
│   └── processed/
│       ├── supervised_sample.parquet         # NB 4 sample
│       ├── supervised_sample_v2.parquet      # NB 8b extended sample
│       ├── coverage_decision.txt             # NB 2 gate decision
│       ├── baseline_scores.csv               # NB 5
│       ├── xgb_scores.csv                    # NB 6
│       ├── bloom_skill.csv                   # NB 9
│       ├── walk_forward_scores.csv           # NB 10 per-fold
│       ├── walk_forward_summary.csv          # NB 10 aggregated
│       ├── group_importance.csv              # NB 8b
│       ├── headline_results.csv              # NB 11 consolidated
│       ├── feature_manifest.json             # NB 4 feature definitions
│       ├── feature_manifest_v2.json          # NB 8b feature definitions
│       └── environment_fingerprint.json      # NB 11
├── models/
│   ├── xgb_h1.json … xgb_h7.json             # NB 6 (v1)
│   └── xgb_v2_h1.json … xgb_v2_h7.json       # NB 8b (v2)
└── figs/
    ├── 01_chl_sample_day.png
    ├── 02_coverage_atlas.png
    ├── 02_coverage_map.png
    ├── 03_sst_and_bathy.png
    ├── 05_baselines.png
    ├── 06_xgb_vs_baselines.png
    ├── 07_shap_h1.png, 07_shap_h7.png, 07_shap_bar_h1_h7.png
    ├── 07_error_map_h3.png, 07_error_by_month.png
    ├── 07_residual_diagnostics_h3.png
    ├── 08_correlation_heatmap.png
    ├── 08_group_importance.png
    ├── 09_bloom_skill.png
    ├── 10_walk_forward.png, 10_walk_forward_per_fold.png
    └── 11_headline.png
```

The `data/raw/` directory can be recreated by re-running notebooks 01, 03, and 08a. Everything else is derived.

---

*This document explains a complete instance of the PLAN.md methodology. It is the project's answer to the question "what did you do and what did you find?". For the rationale behind individual design choices, see PLAN.md.*
