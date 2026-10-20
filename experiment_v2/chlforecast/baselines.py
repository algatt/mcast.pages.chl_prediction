"""The simple rules every model is compared with (step 05)."""

import numpy as np


def fit_damped_persistence(observed, persistence, clim_log):
    """Fit the blend log10(future) = a + b·log10(latest) + c·climatology
    by least squares on training rows. Returns [a, b, c]."""
    design = np.column_stack([
        np.ones(np.asarray(observed).size),
        np.log10(persistence),
        clim_log,
    ])
    usable = np.isfinite(design).all(axis=1) & np.isfinite(np.log10(observed))
    coefficients, *_ = np.linalg.lstsq(design[usable], np.log10(observed)[usable], rcond=None)
    return coefficients


def damped_persistence(coefficients, persistence, clim_log):
    """The blend forecast in mg/m³. Without a recent observation, the climatology."""
    a, b, c = coefficients
    latest_log = np.log10(persistence)
    blended = a + b * latest_log + c * np.asarray(clim_log)
    return 10.0 ** np.where(np.isfinite(latest_log), blended, clim_log)


def baseline_predictions(persistence, clim_log, coefficients, climatology_label="Climatology (2017–2023)"):
    """All three simple rules, in mg/m³."""
    return {
        "Persistence": np.asarray(persistence, dtype="float64"),
        climatology_label: 10.0 ** np.asarray(clim_log, dtype="float64"),
        "Damped persistence": damped_persistence(coefficients, persistence, clim_log),
    }
