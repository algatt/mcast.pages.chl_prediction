My proposed starting setup is:

- Train and evaluate over 2019–2025, the common complete-year period for the three core datasets.
- Preserve missing values and add missingness masks, time since last valid observation, observation counts, and causal rolling statistics.
- Add day-of-year sine/cosine features without downloading another dataset.
- Simulate the NRT publication cutoffs during evaluation: a forecast issued today can use only observations already published today.
- Evaluate against valid future L3 CHL observations. Missing future CHL pixels remain unlabelled.
  We will also need to harmonize the SST and wind grids with CHL. Resampling them onto a 1 km grid does not give those measurements 1 km spatial detail. The MY and NRT SST grids differ, so that transition needs explicit validation before deployment.
