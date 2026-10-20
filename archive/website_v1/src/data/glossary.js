export const glossary = [
  {
    slug: 'chl-a', term: 'Chlorophyll-a', aliases: ['CHL', 'chl-a'], category: 'ocean',
    short: 'A photosynthetic pigment used as a satellite-derived indicator of surface phytoplankton biomass.',
    long: 'Chlorophyll-a is estimated from ocean colour and reported here in mg m⁻³. It is a useful proxy for surface biological activity, but it is not a direct count of organisms and can carry retrieval uncertainty.',
    seeAlso: ['l3', 'log-scale'],
  },
  {
    slug: 'phytoplankton', term: 'Phytoplankton', category: 'ocean',
    short: 'Microscopic photosynthetic organisms drifting in aquatic environments.',
    long: 'Phytoplankton support marine food webs and influence carbon cycling. Satellite chlorophyll observes a surface optical signal associated with them, not the entire water-column community.',
    seeAlso: ['chl-a', 'bloom'],
  },
  {
    slug: 'bloom', term: 'Bloom event', category: 'ocean',
    short: 'An observation exceeding a specified local and seasonal chlorophyll threshold.',
    long: 'A bloom is not a universal fixed concentration in this study. The primary rare-event definition is a validation-calibrated monthly 90th percentile at each pixel. A z-score definition is also evaluated.',
    seeAlso: ['f1', 'far', 'pod'],
  },
  {
    slug: 'target-domain', term: 'Observable target domain', category: 'data',
    short: 'Pixels where the chlorophyll product can genuinely provide valid observations.',
    long: 'Coverage is measured against 46,158 target-domain pixels rather than every cell in the rectangular grid. This avoids counting land and permanently invalid pixels as cloud gaps.',
    seeAlso: ['coverage', 'l3'],
  },
  {
    slug: 'coverage', term: 'Target-domain coverage', category: 'data',
    short: 'The percentage of observable-domain pixels with valid chlorophyll on a given day.',
    long: 'Coverage is computed daily before modelling. Winter coverage averaged 50.47%, above the predeclared 25% feasibility threshold for retaining a daily target.',
    seeAlso: ['target-domain', 'l3'],
  },
  {
    slug: 'l3', term: 'Level-3 ocean colour', aliases: ['L3'], category: 'data',
    short: 'Satellite retrievals mapped to a regular grid with invalid or cloud-covered pixels left missing.',
    long: 'The project uses Level-3 chlorophyll as the forecast target and preserves missing values. No interpolated chlorophyll is created for training labels or evaluation.',
    seeAlso: ['nan', 'target-domain'],
  },
  {
    slug: 'nan', term: 'NaN', aliases: ['missing value'], category: 'data',
    short: 'A software representation of a missing numeric value.',
    long: 'A NaN in the chlorophyll record means there was no valid observation at that pixel and date. XGBoost can learn how to route missing predictors, while missing future targets are excluded from scoring.',
    seeAlso: ['l3', 'xgboost'],
  },
  {
    slug: 'reanalysis', term: 'Reanalysis', category: 'data',
    short: 'A physically consistent reconstruction that combines observations with a numerical model.',
    long: 'ERA5 provides atmospheric predictors such as wind. Reanalysis fields are model-informed inputs; they are not treated as observed chlorophyll targets.',
  },
  {
    slug: 'forecast-horizon', term: 'Forecast horizon', aliases: ['lead time', 'H+'], category: 'ml',
    short: 'How far into the future a prediction is made.',
    long: 'H+1 means one day ahead and H+7 means seven days ahead. This project trains and evaluates a separate model for each of seven daily horizons.',
    seeAlso: ['walk-forward'],
  },
  {
    slug: 'persistence', term: 'Persistence baseline', category: 'ml',
    short: 'A forecast that carries the latest available chlorophyll value into the future.',
    long: 'Ocean conditions often change slowly, making persistence difficult to beat at short horizons. Walk-forward model and persistence scores are calculated on exactly matched test rows.',
    seeAlso: ['r-squared', 'walk-forward'],
  },
  {
    slug: 'climatology', term: 'Climatology baseline', category: 'ml',
    short: 'A seasonal reference prediction learned only from the training period.',
    long: 'Climatology asks whether the model improves on typical seasonal conditions. It is reported in the chronological single-split experiment and is constructed without future leakage.',
    seeAlso: ['leakage'],
  },
  {
    slug: 'xgboost', term: 'XGBoost', category: 'ml',
    short: 'A gradient-boosted decision-tree model with native missing-value routing.',
    long: 'XGBoost combines many decision trees and learns default directions for missing predictors. Its fit is predictive rather than causal; importance measures describe model dependence.',
    seeAlso: ['nan', 'permutation', 'ablation'],
  },
  {
    slug: 'walk-forward', term: 'Walk-forward evaluation', category: 'ml',
    short: 'Repeated chronological evaluation in which training expands through time.',
    long: 'Each fold fits on earlier quarters, validates on the next quarter, and tests on the following quarter. Eight folds cover 2022Q1 through 2023Q4 test periods.',
    seeAlso: ['persistence', 'std'],
  },
  {
    slug: 'leakage', term: 'Temporal leakage', category: 'ml',
    short: 'Using information that would not exist when a forecast is issued.',
    long: 'Leakage can make results look artificially strong. Feature construction, climatology, threshold calibration, and train/validation/test splits are constrained so future information cannot enter the fit.',
  },
  {
    slug: 'permutation', term: 'Grouped permutation importance', category: 'ml',
    short: 'The increase in validation error after jointly shuffling a feature group.',
    long: 'Permutation importance measures how much the fitted model uses a group. In this project a retained group must produce a ΔRMSE larger than two permutation standard deviations.',
    seeAlso: ['ablation'],
  },
  {
    slug: 'ablation', term: 'Grouped ablation', category: 'ml',
    short: 'Retraining after removing an entire feature group.',
    long: 'Ablation measures whether other predictors can substitute for a removed group. Negative ΔR² means the retrained model performed worse without that group.',
    seeAlso: ['permutation'],
  },
  {
    slug: 'log-scale', term: 'Log10 scale', aliases: ['log transform'], category: 'stats',
    short: 'A transformation used to make multiplicative chlorophyll variation easier to model.',
    long: 'Chlorophyll spans orders of magnitude. The model predicts log10 chlorophyll, so errors are interpreted on that scale before any transformation back to mg m⁻³.',
    seeAlso: ['chl-a', 'rmse'],
  },
  {
    slug: 'r-squared', term: 'R²', aliases: ['R-squared'], category: 'stats',
    short: 'Variance explained relative to a mean-only prediction; higher is better.',
    long: 'R² = 1 is perfect, R² = 0 matches predicting the mean, and R² can be negative. The primary H+3 walk-forward result is 0.654 ± 0.121 across folds.',
    seeAlso: ['rmse', 'std'],
  },
  {
    slug: 'rmse', term: 'RMSE', aliases: ['root mean squared error'], category: 'stats',
    short: 'A squared-error measure in the same units as the model target; lower is better.',
    long: 'Here RMSE is reported in log10 mg m⁻³. Squaring means larger errors receive more weight than small ones.',
    seeAlso: ['log-scale', 'r-squared'],
  },
  {
    slug: 'std', term: 'Fold standard deviation', aliases: ['SD', 'standard deviation'], category: 'stats',
    short: 'The spread of scores across the eight test quarters.',
    long: 'The walk-forward band is mean ± one fold SD. Because folds overlap in training data and are not independent random samples, the band is descriptive and is not a confidence interval.',
    seeAlso: ['walk-forward'],
  },
  {
    slug: 'f1', term: 'F1 score', category: 'stats',
    short: 'The harmonic mean of event precision and recall; higher is better.',
    long: 'F1 balances missed detections and false alarms, but should still be read with POD, FAR, and event prevalence. The P90 H+3 value is 0.508.',
    seeAlso: ['pod', 'far', 'bloom'],
  },
  {
    slug: 'pod', term: 'POD', aliases: ['probability of detection', 'recall'], category: 'stats',
    short: 'The fraction of observed events detected; higher is better.',
    long: 'POD = TP / (TP + FN). At H+3 the P90 detector has POD = 0.576.',
    seeAlso: ['f1', 'far'],
  },
  {
    slug: 'far', term: 'FAR', aliases: ['false-alarm ratio'], category: 'stats',
    short: 'The fraction of raised alarms that were false; lower is better.',
    long: 'FAR = FP / (TP + FP). At H+3 the P90 detector has FAR = 0.545, a central limitation for deployment.',
    seeAlso: ['f1', 'pod'],
  },
  {
    slug: 'validation-gate', term: 'Validation gate', category: 'stats',
    short: 'A programmatic condition that must pass before the next notebook stage.',
    long: 'The 13-stage pipeline uses gates for data integrity, coverage, temporal leakage, feature/model consistency, baseline skill, event evaluation, and final artifact completeness.',
    seeAlso: ['leakage'],
  },
]

export function findTerm(query) {
  const q = query.toLowerCase()
  return glossary.find(g => g.slug === q || g.term.toLowerCase() === q ||
    (g.aliases || []).some(a => a.toLowerCase() === q))
}

export function byCategory() {
  return glossary.reduce((acc, g) => {
    ;(acc[g.category] = acc[g.category] || []).push(g)
    return acc
  }, {})
}

export const categoryLabels = {
  ocean: 'Ocean science',
  data: 'Observations & products',
  ml: 'Forecasting & modelling',
  stats: 'Evaluation & metrics',
}

