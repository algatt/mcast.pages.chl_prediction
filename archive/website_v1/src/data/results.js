// Validated artifacts from experiment/data/processed.
// Values are rounded only at presentation time; source arrays retain useful precision.

export const HORIZONS = [1, 2, 3, 4, 5, 6, 7]

export const persistence = {
  rmse: [0.103714, 0.122415, 0.133184, 0.137528, 0.146672, 0.153573, 0.155870],
  r2: [0.849708, 0.798845, 0.754198, 0.734706, 0.689298, 0.661958, 0.665030],
}

export const climatology = {
  rmse: [0.134987, 0.135934, 0.134730, 0.134754, 0.134610, 0.133454, 0.133892],
  r2: [0.745405, 0.751962, 0.748456, 0.745297, 0.738298, 0.744729, 0.752832],
}

export const xgbV1 = {
  rmse: [0.096787, 0.111842, 0.118405, 0.122331, 0.128105, 0.132451, 0.133593],
  r2: [0.869112, 0.832092, 0.805721, 0.790097, 0.762980, 0.748551, 0.753936],
}

export const xgbV2Single = {
  rmse: [0.093183, 0.109616, 0.116887, 0.120543, 0.125278, 0.129324, 0.130643],
  r2: [0.878679, 0.838709, 0.810672, 0.796186, 0.773326, 0.760283, 0.764683],
}

export const xgbV2WalkForward = {
  rmse_mean: [0.091411, 0.106142, 0.113115, 0.120881, 0.123557, 0.127666, 0.128395],
  rmse_std: [0.026972, 0.032082, 0.034454, 0.040372, 0.037687, 0.038317, 0.039716],
  r2_mean: [0.774537, 0.702032, 0.654099, 0.581885, 0.556905, 0.530902, 0.535544],
  r2_std: [0.079302, 0.099414, 0.120823, 0.186914, 0.144140, 0.139922, 0.148504],
}

export const walkForwardPersistence = {
  rmse_mean: [0.100497, 0.118107, 0.130063, 0.135844, 0.142577, 0.149590, 0.152872],
  rmse_std: [0.028986, 0.034862, 0.038302, 0.039557, 0.043019, 0.042548, 0.044991],
  r2_mean: [0.728811, 0.634374, 0.545247, 0.479079, 0.414325, 0.357001, 0.337664],
  r2_std: [0.088809, 0.109511, 0.146320, 0.170009, 0.180564, 0.170021, 0.203829],
}

export const perFoldH3 = [
  { quarter: '2022Q1', r2: 0.451060, persistence: 0.278508, kind: 'winter' },
  { quarter: '2022Q2', r2: 0.682393, persistence: 0.611462, kind: 'spring' },
  { quarter: '2022Q3', r2: 0.668944, persistence: 0.586640, kind: 'summer' },
  { quarter: '2022Q4', r2: 0.780242, persistence: 0.671860, kind: 'autumn' },
  { quarter: '2023Q1', r2: 0.503406, persistence: 0.412561, kind: 'winter' },
  { quarter: '2023Q2', r2: 0.683938, persistence: 0.519053, kind: 'spring' },
  { quarter: '2023Q3', r2: 0.666298, persistence: 0.540997, kind: 'summer' },
  { quarter: '2023Q4', r2: 0.796513, persistence: 0.740895, kind: 'autumn' },
]

export const bloomSkill = {
  median5: [0.912178, 0.901017, 0.892624, 0.885437, 0.877304, 0.869981, 0.858614],
  percentile: [0.608334, 0.537742, 0.508241, 0.483597, 0.408522, 0.403603, 0.388098],
  zscore: [0.584558, 0.527718, 0.485683, 0.455582, 0.410674, 0.398133, 0.386857],
}

export const bloomPOD = {
  median5: [0.910220, 0.895650, 0.882729, 0.871722, 0.858448, 0.847748, 0.829056],
  percentile: [0.679729, 0.678966, 0.575984, 0.576572, 0.777582, 0.730797, 0.756622],
  zscore: [0.674030, 0.638869, 0.607128, 0.526176, 0.549902, 0.485312, 0.418519],
}

export const bloomFAR = {
  median5: [0.085855, 0.093552, 0.097257, 0.100410, 0.102993, 0.106589, 0.109643],
  percentile: [0.449489, 0.554849, 0.545244, 0.583556, 0.722965, 0.721215, 0.739017],
  zscore: [0.483944, 0.550488, 0.595275, 0.598311, 0.672296, 0.662495, 0.640350],
}

export const bloomRates = {
  median5: [0.509068, 0.505507, 0.506373, 0.501965, 0.501042, 0.497823, 0.497555],
  percentile: [0.175487, 0.174927, 0.175876, 0.178216, 0.175990, 0.179464, 0.178776],
  zscore: [0.135915, 0.136283, 0.136984, 0.137039, 0.136241, 0.136695, 0.137804],
}

export const groupImportance = [
  { group: 'chl_history', perm: 0.129632, permStd: 0.000420, abl: -0.013778, cols: 9, core: true },
  { group: 'static_time', perm: 0.040604, permStd: 0.000193, abl: -0.018150, cols: 3, core: true },
  { group: 'sst', perm: 0.018574, permStd: 0.000154, abl: -0.007672, cols: 3, core: true },
  { group: 'optics', perm: 0.016491, permStd: 0.000163, abl: -0.003394, cols: 2, core: false },
  { group: 'wind', perm: 0.004141, permStd: 0.000056, abl: -0.008050, cols: 6, core: false },
  { group: 'salinity', perm: 0.001502, permStd: 0.000055, abl: -0.005006, cols: 2, core: false },
  { group: 'currents_ssh', perm: 0.000830, permStd: 0.000023, abl: -0.000991, cols: 4, core: false },
  { group: 'mld', perm: 0.000358, permStd: 0.000053, abl: -0.001006, cols: 3, core: false },
]

export const monthlyCoverage = [
  { month: 'Jan', coverage: 47.47 }, { month: 'Feb', coverage: 57.60 },
  { month: 'Mar', coverage: 55.15 }, { month: 'Apr', coverage: 49.06 },
  { month: 'May', coverage: 53.93 }, { month: 'Jun', coverage: 55.22 },
  { month: 'Jul', coverage: 74.09 }, { month: 'Aug', coverage: 72.47 },
  { month: 'Sep', coverage: 54.41 }, { month: 'Oct', coverage: 62.38 },
  { month: 'Nov', coverage: 51.52 }, { month: 'Dec', coverage: 47.03 },
]

export const studyFacts = {
  period: '2021–2023',
  rows: 360000,
  features: 32,
  groups: 8,
  horizons: 7,
  folds: 8,
  targetDomainPixels: 46158,
  djfCoverage: 50.47,
  zeroCoverageDays: 87,
  modelCount: 7,
}

export const headlineStats = [
  { label: 'Walk-forward R² · H+3', value: '0.654', detail: '±0.121 across 8 quarters' },
  { label: 'Matched persistence · H+3', value: '0.545', detail: 'same rows, same quarters' },
  { label: 'Rare-event F1 · H+3', value: '0.508', detail: 'P90 detector; FAR 0.545' },
  { label: 'Validated feature set', value: '32', detail: '8 groups · 360,000 rows' },
]
