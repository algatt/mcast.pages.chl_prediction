# Observed Ocean — research companion

A Vue 3 + Vite site explaining the validated chlorophyll-a forecasting pipeline in `../experiment/`. It is written for scientific review first, with a plain-language primer for non-specialists.

## Scientific scope

- Region: Malta–Sicily Channel
- Period: 2021–2023
- Supervised sample: 360,000 pixel-days
- Model: seven horizon-specific XGBoost models, H+1 through H+7
- Final inputs: 32 features in eight groups
- Primary evaluation: eight expanding-window quarterly folds
- Primary H+3 result: R² = 0.654 ± 0.121
- Matched H+3 persistence: R² = 0.545 ± 0.146
- Rare-event H+3 result: P90 F1 = 0.508, FAR = 0.545

The site does not claim matched superiority to an L4 target pipeline, operational readiness, cross-region generalisation, or validation beyond the three-year record.

## Routes

- `#/` — reviewer-first evidence summary
- `#/primer` — accessible explanation of the problem and metrics
- `#/methodology` — all 13 notebook stages and validation gates
- `#/data` — source ledger, coverage decision, and feature inventory
- `#/forecast` — interactive actual/predicted/residual viewer plus residual, spatial, seasonal, and SHAP diagnostics
- `#/findings/observation-contract` — Level-3 target and missingness rules
- `#/findings/group-ablation` — grouped permutation and ablation evidence
- `#/findings/walk-forward` — primary temporal generalisation result
- `#/findings/bloom-detection` — rare-event skill and deployment boundary
- `#/glossary` — current terminology and project-specific definitions
- `#/about` — limitations, reproducibility, and scale-up boundary

Hash routing is deliberate so the static build works on subpath hosts without rewrite rules.

## Local development

```bash
cd website
npm install
npm run dev
```

The development server listens on `http://localhost:5173`.

## Validation and build

```bash
npm run build
npm run preview
```

The production build is written to `dist/`. Figures in `public/figs/` are notebook outputs copied from `../experiment/figs/`; chart values in `src/data/results.js` are transcribed from validated artifacts in `../experiment/data/processed/`.

The forecast viewer contains 48 representative 2023 issue dates at every H+1–H+7 horizon. Regenerate its 336 WebP frames from the final v2 models with:

```bash
# from the repository root
.venv/Scripts/python.exe experiment/export_prediction_frames.py
```

The raster interpolation is visualization-only; frame MAE values and reported metrics use the original observed test rows.

## Content maintenance

When results change:

1. Update the corresponding validated artifact in the notebook pipeline.
2. Update `src/data/results.js`.
3. Update the relevant finding, methodology stage, and limitation text.
4. Run `npm run build`.
5. Search for retired claims before publishing.

The social preview image is `public/og.png`. The website itself is the explanatory layer; the numbered notebooks and processed artifacts remain the scientific source of truth.

## Stack

Vue 3, Vue Router, Chart.js via vue-chartjs, Tailwind CSS, and Vite.

## Data attribution

Ocean variables are derived from Copernicus Marine products, atmospheric predictors from ECMWF ERA5, and bathymetry from NOAA ETOPO. Product identifiers and versions are recorded on the Data & evidence page and in the pipeline artifacts.
