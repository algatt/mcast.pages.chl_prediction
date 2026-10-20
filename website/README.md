# Observed Ocean — experiment v2 site

Explains `experiment_v2/` step by step; each step is one notebook. Vue 3 + Vite + Tailwind, hash routing, no chart libraries:
the figures are small Vue components drawing HTML, SVG or canvas.

## Run locally

```bash
npm install
npm run dev          # http://localhost:5173
```

## Page data

Each step page reads a JSON file built from the experiment's downloaded data, so every number on the page
can be regenerated. From the repository root, with the experiment environment:

```bash
experiment_v2/.venv/bin/python website/scripts/build_nb01_data.py   # → src/data/nb01.json
experiment_v2/.venv/bin/python website/scripts/build_nb02_data.py   # → src/data/nb02.json
experiment_v2/.venv/bin/python website/scripts/build_nb03_data.py   # → src/data/nb03.json
experiment_v2/.venv/bin/python website/scripts/build_nb04_data.py   # → src/data/nb04.json
experiment_v2/.venv/bin/python website/scripts/build_nb05_data.py   # → src/data/nb05.json
experiment_v2/.venv/bin/python website/scripts/build_nb06_data.py   # → src/data/nb06.json
experiment_v2/.venv/bin/python website/scripts/build_nb07_data.py   # → src/data/nb07.json
experiment_v2/.venv/bin/python website/scripts/build_nb08_data.py   # → src/data/nb08.json
```

The scripts need the files that notebooks 01, 02, 04 and 05 write (05 and 06: the saved model; 07: the latest live forecast and the NRT archive from notebook 08).

## Adding a step page

1. Write `scripts/build_nbXX_data.py` if the page needs data.
2. Add `src/pages/StepXX.vue`, built on `components/StepLayout.vue`, and register it in `pages` in `src/router.js`.
3. Set `ready: true` for it in `src/data/steps.js`.

## Deploy

```bash
npm run deploy       # builds and pushes dist/ to the gh-pages branch
```

This replaces the published v1 site. Its source stays in `archive/website_v1/`.
