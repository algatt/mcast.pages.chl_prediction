"""Shared code for the chlorophyll forecasting experiment.

The notebooks import from here so that training (04, 05), the live forecast
(07) and the archive (08) all use one copy of each rule:

    config     - settings shared by every step
    features   - the input recipe: quality control, chlorophyll history,
                 climatology, season
    baselines  - the simple rules: persistence, climatology, the blend
    scoring    - forecast scores and the day-resampling bootstrap
    samples    - rows of (issue day, pixel) for model fitting and scoring
    forecast   - issuing forecasts with the saved model, and the blend rule
    archive    - the daily near-real-time archive (step 08)
"""
