"""Bloom probability forecasts and their scores (step 10).

A bloom is a pixel-day whose observed chlorophyll is at least
config.BLOOM_ANOMALY_LOG10 above the usual value for the month, on the log10
scale. Forecasts are probabilities; they are scored with the Brier score, the
mean squared difference between the probability and what happened (1 or 0).
"""

import numpy as np

from . import config


def is_bloom(observed, clim_log):
    """1 where observed chlorophyll is a bloom for its target month, else 0."""
    return (np.log10(observed) - clim_log >= config.BLOOM_ANOMALY_LOG10).astype("int8")


def base_rate_table(bloom, month, pixel, n_pixels, prior_weight=20.0):
    """How often each pixel had a bloom in each calendar month, from training rows.

    Sparse pixel-months are pulled towards that month's area-wide rate, as if
    `prior_weight` extra days at the area-wide rate had been seen. Returns an
    array (12, n_pixels) of probabilities."""
    month_rate = np.array([bloom[month == m].mean() if np.any(month == m) else bloom.mean() for m in range(1, 13)])
    index = (month - 1) * n_pixels + pixel
    count = np.bincount(index, minlength=12 * n_pixels).reshape(12, n_pixels)
    hits = np.bincount(index, weights=bloom, minlength=12 * n_pixels).reshape(12, n_pixels)
    return (hits + prior_weight * month_rate[:, None]) / (count + prior_weight)


def anomaly_rule_table(bloom, anomaly, bins):
    """How often a bloom followed, for each band of the latest observation's
    anomaly (log10 latest − usual value). The last entry is for rows with no
    recent observation. Returns probabilities, one per band plus one."""
    band = np.where(np.isfinite(anomaly), np.digitize(anomaly, bins), len(bins) + 1)
    hits = np.bincount(band, weights=bloom, minlength=len(bins) + 2)
    count = np.bincount(band, minlength=len(bins) + 2)
    return np.where(count > 0, hits / np.maximum(count, 1), bloom.mean())


def anomaly_rule(table, anomaly, bins):
    band = np.where(np.isfinite(anomaly), np.digitize(anomaly, bins), len(bins) + 1)
    return table[band]


def brier(probability, bloom):
    return float(np.mean((probability - bloom) ** 2))


def brier_skill_interval(bloom, forecast, reference, day, n_boot=1000, seed=0):
    """Brier skill score (%) of `forecast` over `reference`: the % reduction in
    the Brier score, with a 95% interval from resampling whole issue days (as
    scoring.log_rmse_gain_interval). Returns (skill, low, high)."""
    _, day_id = np.unique(day, return_inverse=True)
    n_days = day_id.max() + 1
    f = np.bincount(day_id, (forecast - bloom) ** 2, n_days)
    r = np.bincount(day_id, (reference - bloom) ** 2, n_days)

    def skill(weights):
        return 100 * (1 - (weights @ f) / (weights @ r))

    rng = np.random.default_rng(seed)
    resampled = [skill(np.bincount(rng.integers(0, n_days, n_days), minlength=n_days)) for _ in range(n_boot)]
    low, high = np.percentile(resampled, [2.5, 97.5])
    return skill(np.ones(n_days)), low, high


def reliability(probability, bloom, edges=(0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0001)):
    """Mean forecast probability against observed bloom frequency, per band of
    forecast probability. Rows: (low, high, n, mean forecast, observed frequency)."""
    band = np.digitize(probability, edges[1:-1])
    rows = []
    for k in range(len(edges) - 1):
        sel = band == k
        if sel.any():
            rows.append((edges[k], min(edges[k + 1], 1.0), int(sel.sum()),
                         float(probability[sel].mean()), float(bloom[sel].mean())))
    return rows


def warning_scores(probability, bloom, threshold):
    """Scores of a yes/no bloom warning issued when probability ≥ threshold."""
    warn = probability >= threshold
    hits = int(np.sum(warn & (bloom == 1)))
    misses = int(np.sum(~warn & (bloom == 1)))
    false_alarms = int(np.sum(warn & (bloom == 0)))
    return {
        "Threshold": threshold,
        "Warnings": int(warn.sum()),
        "Blooms": hits + misses,
        "Hit rate (%)": 100 * hits / max(hits + misses, 1),
        "False alarm ratio (%)": 100 * false_alarms / max(hits + false_alarms, 1),
        "Critical success index (%)": 100 * hits / max(hits + misses + false_alarms, 1),
    }


def best_threshold(probability, bloom, candidates=np.round(np.arange(0.05, 0.81, 0.01), 2)):
    """The warning threshold with the highest critical success index (hits over
    hits + misses + false alarms), the usual choice for rare events."""
    scores = [warning_scores(probability, bloom, t)["Critical success index (%)"] for t in candidates]
    return float(candidates[int(np.argmax(scores))])


def area_state_inputs(chl, dates, mask, monthly_log_clim, window=30):
    """The state of the whole area over the past `window` days, from chlorophyll
    available at issue time: the average anomaly (log10 observed − usual value)
    and the share of observed pixel-days that were blooms. Blooms vary greatly
    from year to year; these tell a model what kind of year it is in.
    Returns arrays shaped (time, 1, 1), NaN until enough days are observed."""
    from .features import climatology_for_dates

    with np.errstate(divide="ignore", invalid="ignore"):
        anomaly = np.log10(chl) - climatology_for_dates(monthly_log_clim, dates)
    anomaly = np.where(mask[None], anomaly, np.nan)
    ok = np.isfinite(anomaly)
    daily = {"n": ok.sum(axis=(1, 2)).astype("float64"),
             "anomaly": np.where(ok, anomaly, 0).sum(axis=(1, 2)),
             "bloom": (ok & (anomaly >= config.BLOOM_ANOMALY_LOG10)).sum(axis=(1, 2)).astype("float64")}
    # Shift to issue days (available one day late), then sum over the window.
    rolled = {k: np.convolve(_lagged(v, config.CHL_LAG_DAYS), np.ones(window))[:len(v)] for k, v in daily.items()}
    enough = rolled["n"] >= 0.05 * mask.sum() * window       # at least 5% of the possible pixel-days
    with np.errstate(invalid="ignore", divide="ignore"):
        area_anomaly = np.where(enough, rolled["anomaly"] / rolled["n"], np.nan)
        area_bloom = np.where(enough, rolled["bloom"] / rolled["n"], np.nan)
    return {"area_anomaly_30d": area_anomaly.astype("float32")[:, None, None],
            "area_bloom_share_30d": area_bloom.astype("float32")[:, None, None]}


def _lagged(values, lag):
    """Daily totals moved `lag` days later (to the issue day they become available); zeros before."""
    out = np.zeros_like(values, dtype="float64")
    out[lag:] = values[:-lag] if lag else values
    return out
