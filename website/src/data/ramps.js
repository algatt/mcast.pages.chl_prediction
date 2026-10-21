// Sequential colour ramps: one hue each, light → dark (lightness checked to fall
// steadily). One ramp per variable, so a colour always means the same quantity.
export const CHL_RAMP = ['#d8f0ea', '#a6dccf', '#6cc2b1', '#2fa392', '#0d8577', '#0b665d', '#0a4842']
export const SST_RAMP = ['#fde9dc', '#f9c8a8', '#f3a273', '#e67b45', '#cc5a26', '#a3421a', '#732e12']
export const WIND_RAMP = ['#e6e5fb', '#c5c2f3', '#a19be9', '#7d73dc', '#5f51c9', '#4838a6', '#33277a']

// Diverging: blue (below / better) ↔ neutral grey ↔ red (above / worse).
export const DIVERGING_RAMP = ['#184f95', '#3987e5', '#9ec5f4', '#efeee9', '#f4b0a8', '#e34948', '#9e2b2b']
// Neutral sequential, for error sizes.
export const ERROR_RAMP = ['#f1f0ec', '#d4d2ca', '#b0ada3', '#8a877d', '#646157', '#423f37', '#25231d']

// Identity colours for "observed" versus "filled in" (validated as a pair).
export const OBSERVED = '#0d9488'
export const FILLED = '#eb6834'

export function formatChl(value) {
  return `${value < 0.1 ? value.toFixed(3) : value.toFixed(2)} mg/m³`
}

// A chlorophyll layer for GridMap, from values stored as round(log10(CHL) × 1000).
export function chlLayer({ id, label, values, ...rest }) {
  return {
    id,
    label,
    kind: 'sequential',
    values,
    decode: (raw) => 10 ** (raw / 1000),
    ramp: CHL_RAMP,
    domain: [0.05, 1],
    log: true,
    ticks: [0.05, 0.1, 0.2, 0.5, 1],
    tickFormat: (t) => (t === 1 ? '≥1' : `${t}`),
    legendTitle: 'Chlorophyll (mg/m³)',
    legendNote: 'Log scale: each step is a doubling or more.',
    format: formatChl,
    missingLabel: 'No observation (cloud, glint or haze)',
    ...rest,
  }
}

// Bloom probability (step 10): one red hue, light → dark.
export const BLOOM_RAMP = ['#fbe6e4', '#f6c3bf', '#ee9a94', '#e06d66', '#c94b45', '#a33632', '#732623']
export const BLOOM = '#c94b45'
