# Chlorophyll-a Forecasting — Malta–Sicily Channel

Daily chl-a forecasting (H+1 → H+7) for the central Mediterranean, built on **non-interpolated L3 satellite observations** with honest cloud gaps preserved as `NaN` and handled natively by XGBoost.

🌊 **Live site:** <https://algatt.github.io/mcast.pages.chl_prediction/>

---

## Repository layout

```
mcast.pages.chl_prediction/
├── experiment_v2/        # current experiment: notebooks 01–08, model, small results
├── website/              # site for experiment v2, one page per notebook
├── experiment/           # earlier experiment (v1)
└── archive/website_v1/   # the v1 site, kept as source
```

- **`experiment_v2/`** — the current experiment: L3 chlorophyll forecasts 1, 4 and 7 days ahead, trained on 2017–2024 and tested on 2025, with a live near-real-time check and a daily NRT archive.
- **`website/`** — explains experiment v2 notebook by notebook for an interested reader. See [`website/README.md`](website/README.md). Deployed to GitHub Pages via `npm run deploy`.
- **`experiment/`** and **`archive/website_v1/`** — the earlier experiment and its site. The sections below describe that earlier experiment.

## Headline results

| | H+1 | H+3 | H+7 |
|---|---|---|---|
| **Walk-forward R²** | 0.78 ± 0.08 | 0.65 ± 0.12 | 0.53 ± 0.15 |
| **Persistence R²** (baseline) | 0.80 | 0.69 | 0.63 |
| **Bloom-detection F1** (percentile) | 0.71 | 0.67 | 0.63 |

Averaged across 8 quarterly walk-forward folds. The model matches the reported L4-based ≈ 0.85 at H+1 on a single-split test — without ever training on gap-filled data.

## Quickstart

### Reproduce the science

```bash
# from experiment/
python -m venv .venv
.venv\Scripts\activate                # Windows PowerShell
pip install -r requirements.txt
copernicusmarine login                 # once, cached
jupyter lab                            # then run 00-*.ipynb → 11-*.ipynb in order
```

Total runtime: a few hours (mostly downloads). ~8 GB of raw NetCDFs land in `experiment/data/raw/` — ignored by git (recreatable).

### Run the website locally

```bash
# from website/
npm install
npm run dev                            # http://localhost:5173
```

Deploy to GitHub Pages:

```bash
npm run deploy                         # builds + pushes dist/ to gh-pages branch
```

## Data sources

All data is public and free, pulled at build time by the notebooks:

- **Chlorophyll-a (L3, target):** Copernicus Marine
- **SST, salinity, currents, SSH, MLD, KD490:** Copernicus Marine
- **Wind:** ERA5 via Copernicus Climate Data Store
- **Bathymetry:** NOAA ETOPO 2022 via PIFSC ERDDAP

No raw data is committed to this repo (the `.gitignore` keeps NetCDFs out) — everything is re-downloadable from the sources above.

## License

Code: MIT. Data provenance and terms of use per each source above.
