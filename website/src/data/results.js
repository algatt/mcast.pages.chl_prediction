// All numbers pulled from the actual notebook runs.
// See experiment/data/processed/*.csv and EXPLANATION.md for provenance.

export const HORIZONS = [1, 2, 3, 4, 5, 6, 7]

// ── Baselines (Notebook 5) ───────────────────────────────────────
export const persistence = {
  rmse: [0.097, 0.109, 0.119, 0.123, 0.129, 0.139, 0.135],
  r2:   [0.804, 0.736, 0.690, 0.678, 0.635, 0.574, 0.630],
}
export const climatology = {
  rmse: [0.144, 0.145, 0.143, 0.148, 0.134, 0.140, 0.144],
  r2:   [0.527, 0.516, 0.535, 0.515, 0.568, 0.565, 0.571],
}

// ── XGB v1 single-split (Notebook 6) ─────────────────────────────
export const xgbV1 = {
  rmse: [0.088, 0.097, 0.105, 0.104, 0.107, 0.114, 0.113],
  r2:   [0.838, 0.792, 0.761, 0.770, 0.749, 0.710, 0.741],
}

// ── XGB v2 single-split (Notebook 8b) ────────────────────────────
export const xgbV2Single = {
  rmse: [0.088, 0.097, 0.105, 0.104, 0.107, 0.114, 0.113],
  r2:   [0.864, 0.805, 0.784, 0.783, 0.759, 0.727, 0.751],
}

// ── XGB v2 walk-forward (Notebook 10) ────────────────────────────
export const xgbV2WalkForward = {
  rmse_mean: [0.092, 0.108, 0.115, 0.119, 0.123, 0.133, 0.132],
  rmse_std:  [0.025, 0.033, 0.034, 0.036, 0.038, 0.044, 0.044],
  r2_mean:   [0.776, 0.698, 0.653, 0.608, 0.575, 0.506, 0.530],
  r2_std:    [0.077, 0.103, 0.117, 0.137, 0.139, 0.162, 0.153],
}

// Per-fold breakdown at H+3 (Notebook 10 per-fold CSV)
export const perFoldH3 = [
  { quarter: '2022Q1', r2: 0.460, kind: 'winter' },
  { quarter: '2022Q2', r2: 0.711, kind: 'spring' },
  { quarter: '2022Q3', r2: 0.658, kind: 'summer' },
  { quarter: '2022Q4', r2: 0.784, kind: 'autumn' },
  { quarter: '2023Q1', r2: 0.519, kind: 'winter' },
  { quarter: '2023Q2', r2: 0.647, kind: 'spring' },
  { quarter: '2023Q3', r2: 0.649, kind: 'summer' },
  { quarter: '2023Q4', r2: 0.795, kind: 'autumn' },
]

// ── Bloom-detection F1 (Notebook 9) ──────────────────────────────
export const bloomSkill = {
  siegel:     [0.694, 0.635, 0.634, 0.591, 0.604, 0.589, 0.588],
  percentile: [0.713, 0.667, 0.668, 0.647, 0.647, 0.639, 0.631],
  zscore:     [0.709, 0.670, 0.667, 0.646, 0.641, 0.635, 0.627],
}
export const bloomPOD = {
  siegel:     [0.693, 0.645, 0.685, 0.615, 0.600, 0.610, 0.627],
  percentile: [0.723, 0.685, 0.716, 0.682, 0.658, 0.659, 0.673],
  zscore:     [0.716, 0.682, 0.713, 0.670, 0.646, 0.649, 0.657],
}
export const bloomFAR = {
  siegel:     [0.306, 0.375, 0.411, 0.431, 0.392, 0.430, 0.447],
  percentile: [0.296, 0.349, 0.373, 0.385, 0.364, 0.380, 0.406],
  zscore:     [0.299, 0.342, 0.374, 0.376, 0.363, 0.379, 0.401],
}

// ── Group importance (Notebook 8b) ───────────────────────────────
export const groupImportance = [
  { group: 'chl_history',  perm: 0.1102, abl: -0.0063, cols: 8, core: true  },
  { group: 'static_time',  perm: 0.0073, abl: -0.0169, cols: 3, core: true  },
  { group: 'optics',       perm: 0.0099, abl: -0.0016, cols: 2, core: false },
  { group: 'sst',          perm: 0.0034, abl: -0.0030, cols: 3, core: true  },
  { group: 'wind',         perm: 0.0002, abl: -0.0037, cols: 6, core: false },
  { group: 'salinity',     perm: 0.0014, abl: -0.0033, cols: 2, core: false },
  { group: 'currents_ssh', perm: 0.0010, abl: -0.0035, cols: 4, core: false },
  { group: 'mld',          perm: 0.0003, abl: -0.0012, cols: 3, core: false },
]

// ── Coverage atlas (Notebook 2) ──────────────────────────────────
export const monthlyCoverage = [
  { month: 'Jan', coverage: 40.7 }, { month: 'Feb', coverage: 49.4 },
  { month: 'Mar', coverage: 47.3 }, { month: 'Apr', coverage: 42.0 },
  { month: 'May', coverage: 46.2 }, { month: 'Jun', coverage: 47.3 },
  { month: 'Jul', coverage: 63.5 }, { month: 'Aug', coverage: 62.1 },
  { month: 'Sep', coverage: 46.6 }, { month: 'Oct', coverage: 53.5 },
  { month: 'Nov', coverage: 44.2 }, { month: 'Dec', coverage: 40.3 },
]

// ── Headline stats for the hero ──────────────────────────────────
export const headlineStats = [
  { label: 'R² @ H+1',        value: '0.78',   detail: '± 0.08 walk-forward' },
  { label: 'R² @ H+3',        value: '0.65',   detail: '± 0.12 walk-forward' },
  { label: 'Bloom F1 @ H+3',  value: '0.67',   detail: 'percentile definition' },
  { label: 'Walk-forward folds', value: '8',   detail: 'quarterly, expanding window' },
]
