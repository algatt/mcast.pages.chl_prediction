"""Rows of (issue day, pixel) for fitting and scoring models (step 05)."""

import numpy as np
import pandas as pd


def make_samples(model_data, splits, horizon, predictors, fraction=1.0, seed=0):
    """Every (issue day, pixel) in `splits` with an observed target `horizon` days later.

    `model_data` is the prepared dataset from step 04. Returns a dict with the
    inputs `X`, the `observed` target, the `persistence` and target-day
    `clim_log` values for the baselines, the `day` index and `target_month`.
    """
    splits = [splits] if isinstance(splits, str) else list(splits)
    in_split = np.zeros(model_data.sizes["time"], dtype=bool)
    for split in splits:
        in_split |= model_data[f"split_{split}"].values == 1
    days = np.flatnonzero(in_split)

    # Read one contiguous block of dates: netCDF reads a list of dates with
    # gaps one day at a time, which is hundreds of times slower. Days in the
    # block that belong to no requested split are excluded through `valid`.
    block = slice(days[0], days[-1] + 1)
    subset = model_data.isel(time=block)
    in_block = in_split[block]
    mask = model_data["model_mask"].values == 1

    def grid(name, data=subset):
        return data[name].transpose("time", "latitude", "longitude").values

    target = grid(f"chl_target_{horizon}d")
    valid = np.isfinite(target) & (target > 0) & mask[None] & in_block[:, None, None]
    t, i, j = np.nonzero(valid)

    if fraction < 1.0:
        keep = np.random.default_rng(seed).random(t.size) < fraction
        t, i, j = t[keep], i[keep], j[keep]

    columns = {}
    for name in predictors:
        dims = subset[name].dims
        if dims == ("time",):
            columns[name] = subset[name].values[t]
        elif dims == ("latitude",):
            columns[name] = subset[name].values[i]
        elif dims == ("longitude",):
            columns[name] = subset[name].values[j]
        else:
            columns[name] = grid(name)[t, i, j]

    # Climatology for the target date: the issue-month value h days later.
    target_clim = model_data["chl_clim_log"].shift(time=-horizon).isel(time=block)

    return {
        "X": pd.DataFrame(columns).astype("float32"),
        "observed": target[t, i, j].astype("float64"),
        "persistence": grid("chl_latest")[t, i, j].astype("float64"),
        "clim_log": grid("chl_clim_log", target_clim.to_dataset())[t, i, j].astype("float64"),
        "day": t,
        "pixel": (i, j),
        "target_month": (pd.DatetimeIndex(subset.time.values[t]) + pd.Timedelta(days=horizon)).month.to_numpy(),
    }


def rows_from_arrays(arrays, target, days, mask, fraction=1.0, seed=0):
    """Rows of (issue day, pixel) from in-memory arrays (step 09).

    `arrays` maps input names to arrays shaped (time, latitude, longitude) (or
    broadcastable to it); `target` is the observed chlorophyll `horizon` days
    later on the same calendar; `days` is a boolean selection of issue days.
    Returns the inputs `X`, the `observed` target and the row positions.
    """
    valid = np.isfinite(target) & (target > 0) & mask[None] & np.asarray(days)[:, None, None]
    t, i, j = np.nonzero(valid)
    if fraction < 1.0:
        keep = np.random.default_rng(seed).random(t.size) < fraction
        t, i, j = t[keep], i[keep], j[keep]
    X = pd.DataFrame({name: np.broadcast_to(values, target.shape)[t, i, j] for name, values in arrays.items()})
    return {"X": X.astype("float32"), "observed": target[t, i, j].astype("float64"), "t": t, "i": i, "j": j}
