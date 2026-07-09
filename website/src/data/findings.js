// The four headline findings, used for the Home page cards and Findings routes.

export const findings = [
  {
    slug: 'l3-vs-l4',
    number: '01',
    title: 'L3 + native NaN matches the L4 baseline',
    tagline: 'The methodological bet paid off',
    summary:
      'Using honest cloud gaps as NaN in the target — and letting XGBoost handle them natively — we hit R² = 0.86 at H+1 on the test set, matching the R² ≈ 0.85 reported by L4-based systems. Without ever training on gap-filled data.',
    metric: { label: 'H+1 test R²', value: '0.86', vs: 'vs 0.85 L4 baseline' },
    color: 'from-ocean-500 to-ocean-700',
    icon: '🌊',
  },
  {
    slug: 'group-ablation',
    number: '02',
    title: 'Every group helps, none is a silver bullet',
    tagline: 'Permutation and ablation tell different stories',
    summary:
      'Grouped permutation says chl_history dominates 10×. Grouped ablation says static_time (depth + DOY) is the most essential. Both are right — the divergence itself is the finding. Collectively the six new covariate groups add +0.024 R² at H+3.',
    metric: { label: 'Collective lift', value: '+0.024 R²', vs: 'over chl-history baseline' },
    color: 'from-emerald-500 to-teal-700',
    icon: '🧩',
  },
  {
    slug: 'walk-forward',
    number: '03',
    title: 'The single split was systematically lucky',
    tagline: 'Winter is much harder than the headline suggested',
    summary:
      'Across 8 quarterly walk-forward folds, R² at H+3 is 0.65 ± 0.12 — not the 0.78 the single split showed. The chronological split landed on autumn 2023 (an easy quarter). Winter quarters are 0.15–0.30 R² harder. The error bar is itself a result.',
    metric: { label: 'H+3 R² (WF)', value: '0.65 ± 0.12', vs: 'vs 0.78 single-split' },
    color: 'from-amber-500 to-orange-600',
    icon: '📊',
  },
  {
    slug: 'bloom-detection',
    number: '04',
    title: 'Bloom detection works across three definitions',
    tagline: 'F1 ≥ 0.59 at every horizon, three ways',
    summary:
      'Siegel (median+5%), P90 percentile, and z-score anomaly — three independent bloom definitions — all clear F1 = 0.5 at every horizon from H+1 to H+7. POD stays 0.6–0.7, FAR stays below 0.45. Operationally deployable.',
    metric: { label: 'H+1 F1', value: '0.71', vs: 'percentile definition' },
    color: 'from-chl-500 to-emerald-700',
    icon: '🌱',
  },
]
