export const findings = [
  {
    slug: 'observation-contract',
    number: '01',
    eyebrow: 'Observation contract',
    title: 'The target remains observed, even when the ocean is hidden',
    tagline: 'L3 gaps are retained; no synthetic chlorophyll targets are created.',
    summary:
      'The pipeline defines an observable CHL domain, measures coverage against that domain, and keeps missing issue-time CHL as NaN. The daily target was selected only after winter coverage cleared the predeclared 25% feasibility threshold.',
    metric: { label: 'DJF target coverage', value: '50.47%', vs: 'daily target retained' },
    tone: 'cyan',
  },
  {
    slug: 'group-ablation',
    number: '02',
    eyebrow: 'Feature evidence',
    title: 'All eight feature groups survived two independent tests',
    tagline: 'Permutation asks what the model uses; ablation asks what it needs.',
    summary:
      'The final 32-feature model retains CHL history, SST, static/time, salinity, currents/SSH, MLD, optics, and wind. Every new group lowered validation R² when removed and produced a measurable grouped-permutation signal.',
    metric: { label: 'H+3 single-split lift', value: '+0.005 R²', vs: 'v2 0.811 vs v1 0.806' },
    tone: 'green',
  },
  {
    slug: 'walk-forward',
    number: '03',
    eyebrow: 'Temporal robustness',
    title: 'The single-year score overstates general performance',
    tagline: 'Quarterly walk-forward evaluation exposes temporal sensitivity.',
    summary:
      'H+3 falls from 0.811 on the 2023 single split to 0.654 ± 0.121 across eight expanding-window test quarters. The model still beats persistence on the same rows at every horizon, but the variability is part of the result.',
    metric: { label: 'H+3 walk-forward R²', value: '0.654 ± 0.121', vs: 'persistence 0.545 ± 0.146' },
    tone: 'amber',
  },
  {
    slug: 'bloom-detection',
    number: '04',
    eyebrow: 'Event detection',
    title: 'Rare-bloom skill passes narrowly—and false alarms remain high',
    tagline: 'Useful as a research signal, not yet an operational warning service.',
    summary:
      'The validation-calibrated monthly P90 detector reaches H+3 F1 = 0.508, just above the gate, with FAR = 0.545. Skill drops below 0.50 from H+4 onward. The median+5% series is reported separately as an auxiliary regime diagnostic, not a rare event.',
    metric: { label: 'P90 H+3 F1 / FAR', value: '0.508 / 0.545', vs: '17.6% observed event rate' },
    tone: 'rose',
  },
]
