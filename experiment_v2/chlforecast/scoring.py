"""Forecast scores (step 05)."""

import numpy as np


def chl_scores(observed, predicted):
    """The standard table of scores for one method, in mg/m³ and log10."""
    observed = np.asarray(observed, dtype="float64")
    predicted = np.asarray(predicted, dtype="float64")
    error = predicted - observed
    log_error = np.log10(predicted) - np.log10(observed)
    return {
        "Scored pixel-days": observed.size,
        "Bias (mg/m³)": error.mean(),
        "MAE (mg/m³)": np.abs(error).mean(),
        "RMSE (mg/m³)": np.sqrt(np.mean(error ** 2)),
        "RMSE (log10)": np.sqrt(np.mean(log_error ** 2)),
        "Median relative error (%)": np.median(100 * np.abs(error) / observed),
    }


def log_rmse_gain_interval(observed, model, baseline, day, n_boot=1000, seed=0):
    """% reduction in log10 RMSE versus a baseline, with a 95% interval from
    resampling whole issue days (pixels on one day are not independent).
    Returns (gain, low, high)."""
    log_observed = np.log10(observed)
    _, day_id = np.unique(day, return_inverse=True)
    n_days = day_id.max() + 1

    def daily_sums(predicted):
        squared = (np.log10(predicted) - log_observed) ** 2
        return np.bincount(day_id, squared, n_days)

    model_sum, baseline_sum = daily_sums(model), daily_sums(baseline)
    counts = np.bincount(day_id, minlength=n_days)

    def gain(weights):
        n = weights @ counts
        return 100 * (1 - np.sqrt(weights @ model_sum / n) / np.sqrt(weights @ baseline_sum / n))

    rng = np.random.default_rng(seed)
    resampled = [gain(np.bincount(rng.integers(0, n_days, n_days), minlength=n_days)) for _ in range(n_boot)]
    low, high = np.percentile(resampled, [2.5, 97.5])
    return gain(np.ones(n_days)), low, high
