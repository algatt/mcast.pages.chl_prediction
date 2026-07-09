# Chl-a Forecasting — Web Report

A Vue 3 + Vite + Tailwind CSS site that walks through the methodology and results
of the Malta–Sicily Channel chlorophyll-a forecasting project. Content is derived
from [`../experiment/EXPLANATION.md`](../experiment/EXPLANATION.md); figures come from
[`../experiment/figs/`](../experiment/figs/) (copied into `public/figs/` at build time).

## Stack

| Tool         | Version | Why |
|--------------|---------|-----|
| Vue 3        | ^3.4    | Composition API, `<script setup>` throughout |
| Vite         | ^5.4    | Fast dev server + optimised build |
| Vue Router 4 | ^4.4    | Hash history (no server rewrite needed on GH Pages) |
| Tailwind CSS | ^3.4    | Utility-first styling; `@tailwindcss/typography` for prose |
| Chart.js     | ^4.4    | Interactive charts (via `vue-chartjs`) |

## Site structure

- **`/`** — Hero + four finding cards + live skill chart teaser
- **`/methodology`** — 12-stage vertical timeline with gate outcomes and inline figures
- **`/data`** — every dataset used, resolution, coverage atlas
- **`/findings/l3-vs-l4`** — Finding 01: L3 + native NaN matches L4 baseline
- **`/findings/group-ablation`** — Finding 02: every group helps, none is a silver bullet
- **`/findings/walk-forward`** — Finding 03: single split was systematically lucky
- **`/findings/bloom-detection`** — Finding 04: F1 ≥ 0.5 across 3 definitions
- **`/about`** — limitations, repo layout, scale-up plan

Each finding page has interactive components — horizon sliders, metric switches,
tabbed views — powered by Chart.js.

## Local dev

```bash
# from the website/ folder
npm install
npm run dev            # http://localhost:5173
```

The dev server auto-opens the browser. Hot-reload works for `.vue`, `.js`, and CSS.

## Build

```bash
npm run build          # produces dist/
npm run preview        # serves dist/ locally at http://localhost:4173
```

## Deploy to GitHub Pages

The site uses **hash-based routing** (`createWebHashHistory`) so it works on any
static host — including GH Pages project pages — with no server-side rewriting.

### One-time setup

1. Push this repo to GitHub (root of the repo is fine; `website/` is a subdirectory).
2. On GitHub → Settings → Pages, set **Source** to `gh-pages` branch, `/ (root)`.

### Deploy command

```bash
# from the website/ folder
npm run deploy         # runs `npm run build && npx gh-pages -d dist`
```

The `gh-pages` package (already in devDependencies) pushes `dist/` to the
`gh-pages` branch. GitHub Pages serves it from that branch.

### If your GH Pages URL is `<user>.github.io/<repo>/`

Because `vite.config.js` uses `base: './'`, asset paths in the build are relative
to the HTML — they work at any subpath without extra config. The URL will look
like `https://<user>.github.io/<repo>/#/methodology` (note the `#` for hash routing).

If you'd prefer BrowserHistory clean URLs on GH Pages, you'd need a `404.html`
fallback trick — see [vitejs/vite issue #2820](https://github.com/vitejs/vite/discussions/2820).
Hash history is simpler and reliable; recommended.

## Adding a new figure

1. Save the PNG into `public/figs/`
2. Reference it as `figs/my-chart.png` from any component (the leading `./` is added by Vite)

## Updating results

All numbers live in **`src/data/results.js`**. Change a value there and every chart,
table, and stat card updates. Provenance for each number is in
[`../experiment/EXPLANATION.md`](../experiment/EXPLANATION.md) and the corresponding
`../experiment/data/processed/*.csv`.

## File layout

```
website/
├── package.json
├── vite.config.js          # base: './', server on :5173
├── tailwind.config.js      # ocean/chl palette, prose plugin
├── postcss.config.js
├── index.html              # Google Fonts (Inter + JetBrains Mono)
├── public/
│   ├── favicon.svg
│   └── figs/               # 18 PNGs copied from ../experiment/figs/
└── src/
    ├── main.js             # createApp + register Chart.js parts
    ├── router.js           # hash history, 8 routes
    ├── App.vue             # NavBar + <router-view> + Footer
    ├── style.css           # Tailwind + custom @layer components
    ├── data/
    │   ├── results.js      # all numbers (persistence, xgb, walk-forward, bloom, ...)
    │   ├── findings.js     # the 4 headline findings
    │   └── stages.js       # 12 pipeline stages for Methodology page
    ├── components/
    │   ├── NavBar.vue, Footer.vue
    │   ├── StatCard.vue, FindingCard.vue, FigureCard.vue, SectionHeader.vue
    │   ├── SkillChart.vue, BloomChart.vue, AblationChart.vue
    │   ├── CoverageChart.vue, PerFoldChart.vue
    │   └── HorizonSlider.vue
    └── pages/
        ├── Home.vue, Methodology.vue, Data.vue, About.vue
        ├── FindingL3.vue, FindingAblation.vue
        ├── FindingWalkForward.vue, FindingBloom.vue
```

## Design notes

- **Fonts**: Inter (body) + JetBrains Mono (code/tabular). Loaded from Google Fonts.
- **Palette**: custom `ocean-*` (blues) and `chl-*` (greens) in `tailwind.config.js`.
- **Numbers**: `tabular-nums` class on every metric so digits align.
- **Charts**: Chart.js line + bar, no external annotation plugins. Walk-forward error
  bars are drawn as a filled area between (mean + σ) and (mean − σ) series with
  invisible borders.
- **Interactivity**: horizon slider is a plain `<input type="range">` with
  Tailwind's `accent-*` utility to colour the thumb. Tab switches on the finding
  pages use pure Vue reactive refs — no third-party UI library.

## License

Code: MIT. Data provenance: CMEMS (`https://data.marine.copernicus.eu`), NOAA ETOPO,
ECMWF ERA5 (`https://cds.climate.copernicus.eu`).
