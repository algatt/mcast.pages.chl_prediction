"""Settings shared by every step. Change them here, not in a notebook."""

from pathlib import Path

# The experiment folder (experiment_v2/), wherever this package is imported from.
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
PROCESSED = DATA / "processed"
ARCHIVE_DIR = DATA / "raw" / "nrt_archive"
# The first model (steps 05–06), kept as the record of those results.
STEP05_MODEL_PATH = BASE / "models" / "chl_forecast_1_4_7d.joblib"
# The model in use (promoted in step 09); the live forecast (step 07) uses it.
MODEL_PATH = BASE / "models" / "chl_forecast_step09.joblib"
STEP09_CANDIDATE_PATH = BASE / "models" / "chl_forecast_candidate_step09.joblib"

REGION = {
    "minimum_longitude": 13.90,
    "maximum_longitude": 15.20,
    "minimum_latitude": 35.55,
    "maximum_latitude": 36.90,
}

FORECAST_ISSUE_TIME_UTC = "20:30"
FORECAST_HORIZONS = (1, 4, 7)

# Days between a measurement and the issue day on which it is first usable.
CHL_LAG_DAYS = 1
SST_LAG_DAYS = 0
WIND_LAG_DAYS = 1

CHL_HISTORY_DAYS = 7

# Quality control (step 04).
MAX_PLAUSIBLE_CHL = 10.0
# Added in step 09: used by the model in use and the live forecast (step 07).
MIN_PLAUSIBLE_CHL = 0.01
MIN_TRAINING_OBSERVATIONS = 200

SPLIT_PERIODS = {
    "train": ("2017-01-01", "2023-12-31"),
    "validation": ("2024-01-01", "2024-12-31"),
    "test": ("2025-01-01", "2025-12-31"),
}

CORE_FEATURES = [
    "season_sin", "season_cos",
    "chl_latest", "chl_age_days",
    "chl_mean_7d", "chl_observations_7d",
    "latitude_deg", "longitude_deg",
]
# Inputs of the step 05 model.
FINAL_FEATURES = CORE_FEATURES + ["chl_clim_log", "sst_c", "sst_observed"]

EXTRA_FEATURES = [
    "chl_nbr5_yesterday", "chl_nbr15_7d",
    "chl_trend_log", "chl_anomaly_log",
    "sst_anomaly", "sst_change_7d",
    "coast_distance_km",
]

# Inputs of the model in use (step 09): the step 05 inputs plus the new ones.
MODEL_FEATURES = FINAL_FEATURES + EXTRA_FEATURES

# Bloom prediction (step 10): a bloom is chlorophyll at least 10**0.2 ≈ 1.6 times
# the usual value for the month (the "high-chlorophyll days" of steps 05 and 09).
BLOOM_ANOMALY_LOG10 = 0.2
BLOOM_MODEL_PATH = BASE / "models" / "bloom_step10.joblib"
