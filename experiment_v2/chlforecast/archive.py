"""The daily near-real-time archive (step 08).

Saves every day the live Copernicus feed offers that is not already saved,
one file per day per product, and never overwrites. Used by
08-NRT-Archive.ipynb and by the scheduled job:

    cd experiment_v2 && .venv/bin/python -m chlforecast.archive
"""

from datetime import datetime, timezone
import sys

import numpy as np
import pandas as pd
import xarray as xr

from . import config

SOURCES = {
    "chl": {
        "dataset_id": "cmems_obs-oc_med_bgc-plankton_nrt_l3-multi-1km_P1D",
        "variable": "CHL",
        "margin": 0.0,
        "recent_days": None,      # keep every day the rolling window offers
        "lag_days": config.CHL_LAG_DAYS,
    },
    "chl_l4": {
        "dataset_id": "cmems_obs-oc_med_bgc-plankton_nrt_l4-gapfree-multi-1km_P1D",
        "variable": "CHL",
        "margin": 0.0,
        "recent_days": None,
        "lag_days": config.CHL_LAG_DAYS,
    },
    "sst": {
        "dataset_id": "SST_MED_SST_L3S_NRT_OBSERVATIONS_010_012_a",
        "variable": "adjusted_sea_surface_temperature",
        "margin": 0.07,           # covers the edge SST cells, as in step 07
        "recent_days": 30,        # the SST record goes back to 2008
        "lag_days": config.SST_LAG_DAYS,
    },
}


def open_sources():
    """Open each live dataset (lazily; no data is downloaded yet)."""
    import copernicusmarine

    remote = {}
    for name, source in SOURCES.items():
        catalogue = copernicusmarine.describe(dataset_id=source["dataset_id"])
        dataset = next(
            d for product in catalogue.products for d in product.datasets
            if d.dataset_id == source["dataset_id"]
        )
        version = dataset.versions[0].label
        data = copernicusmarine.open_dataset(
            dataset_id=source["dataset_id"],
            dataset_version=version,
            variables=[source["variable"]],
            minimum_longitude=config.REGION["minimum_longitude"] - source["margin"],
            maximum_longitude=config.REGION["maximum_longitude"] + source["margin"],
            minimum_latitude=config.REGION["minimum_latitude"] - source["margin"],
            maximum_latitude=config.REGION["maximum_latitude"] + source["margin"],
        )
        data = data.rename({
            old: new for old, new in [("lat", "latitude"), ("lon", "longitude")]
            if old in data.coords and new not in data.coords
        })
        remote[name] = {"data": data, "version": version}
    return remote


def offered(remote):
    """What each live dataset currently offers."""
    rows = []
    for name, r in remote.items():
        times = pd.DatetimeIndex(r["data"].time.values)
        rows.append({"Source": name, "Version": r["version"], "Days offered": len(times),
                     "First": f"{times.min():%Y-%m-%d}", "Latest": f"{times.max():%Y-%m-%d}"})
    return pd.DataFrame(rows).set_index("Source")


def save_new_days(remote, archive_dir=None):
    """Save every offered day not yet in the archive. Returns the log rows."""
    archive_dir = archive_dir or config.ARCHIVE_DIR
    retrieved_utc = pd.Timestamp.now(tz="UTC")
    rows = []

    for name, source in SOURCES.items():
        data = remote[name]["data"]
        variable = source["variable"]
        days = pd.DatetimeIndex(data.time.values)
        if source["recent_days"]:
            newest = days.max().normalize()
            days = days[days >= newest - pd.Timedelta(days=source["recent_days"] - 1)]

        out_dir = archive_dir / name
        out_dir.mkdir(parents=True, exist_ok=True)

        for day in days:
            path = out_dir / f"{day:%Y-%m-%d}.nc"
            row = {"Source": name, "Date": f"{day:%Y-%m-%d}"}

            field = data[[variable]].sel(time=[day]).load()
            valid = int(np.isfinite(field[variable]).sum().item())

            # The first copy is never overwritten. If the live feed now offers
            # different values for the day (an early file completed later, or a
            # reprocessing), that version is kept too, under revisions/.
            if path.exists():
                if _same_values(path, field, variable) or _same_as_a_revision(out_dir, day, field, variable):
                    rows.append({**row, "Status": "Already archived"})
                    continue
                stamp = retrieved_utc.strftime("%Y%m%dT%H%M%SZ")
                path = out_dir / "revisions" / f"{day:%Y-%m-%d}_{stamp}.nc"
                path.parent.mkdir(exist_ok=True)
                row["Status"] = "Revised: new version kept"
            field.attrs.update({
                "source_dataset_id": source["dataset_id"],
                "source_dataset_version": remote[name]["version"],
                "retrieved_utc": retrieved_utc.isoformat(),
                "archive_note": "First retrieved copy; never overwritten",
            })
            for v in field.variables:
                field[v].encoding = {}

            # Write under a temporary name first, so an interrupted run never
            # leaves a half-written file that looks complete.
            partial = path.with_name(path.name + ".part")
            field.to_netcdf(partial, encoding={variable: {"zlib": True, "complevel": 4}})
            partial.rename(path)
            rows.append({"Status": "Saved", **row, "Valid pixels": valid})

    log = pd.DataFrame(rows)
    log["Retrieved (UTC)"] = retrieved_utc.isoformat()
    # Fixed column order: the log file is appended to on every run.
    log = log.reindex(columns=["Source", "Date", "Status", "Valid pixels", "Retrieved (UTC)"])
    log_path = archive_dir / "archive_log.csv"
    log.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
    return log


def _same_values(path, field, variable):
    with xr.open_dataset(path) as stored:
        return np.array_equal(stored[variable].values, field[variable].values, equal_nan=True)


def _same_as_a_revision(out_dir, day, field, variable):
    return any(_same_values(p, field, variable)
               for p in sorted((out_dir / "revisions").glob(f"{day:%Y-%m-%d}_*.nc")))


def versions(source, archive_dir=None):
    """Every stored version of every day: (date, retrieved_utc, path), oldest first."""
    archive_dir = archive_dir or config.ARCHIVE_DIR
    rows = []
    for path in (archive_dir / source).glob("*.nc"):
        rows.append((path.stem, path))
    for path in (archive_dir / source / "revisions").glob("*.nc"):
        rows.append((path.stem.split("_")[0], path))
    out = []
    for date, path in rows:
        with xr.open_dataset(path) as ds:
            out.append({"date": date, "retrieved_utc": ds.attrs.get("retrieved_utc"), "path": path})
    return sorted(out, key=lambda r: (r["date"], r["retrieved_utc"] or ""))


def issue_cutoff(source, date):
    """When a day's data must have been downloaded to count for the forecast it
    first feeds: FORECAST_ISSUE_TIME_UTC on the day of use."""
    hour, minute = map(int, config.FORECAST_ISSUE_TIME_UTC.split(":"))
    use_day = pd.Timestamp(date) + pd.Timedelta(days=SOURCES[source]["lag_days"])
    return (use_day + pd.Timedelta(hours=hour, minutes=minute)).tz_localize("UTC")


def holdings(archive_dir=None):
    """Days held per source, and any missing days between the first and last."""
    archive_dir = archive_dir or config.ARCHIVE_DIR
    rows = []
    for name in SOURCES:
        files = sorted((archive_dir / name).glob("*.nc"))
        if not files:
            continue
        dates = pd.DatetimeIndex([pd.Timestamp(p.stem) for p in files])
        missing = pd.date_range(dates.min(), dates.max(), freq="D").difference(dates)
        revised = len(list((archive_dir / name / "revisions").glob("*.nc")))
        rows.append({
            "Source": name,
            "Days archived": len(dates),
            "Later versions kept": revised,
            "First": f"{dates.min():%Y-%m-%d}",
            "Last": f"{dates.max():%Y-%m-%d}",
            "Missing days": ", ".join(f"{d:%Y-%m-%d}" for d in missing) or "None",
        })
    return pd.DataFrame(rows).set_index("Source")


def load(source, latitude, longitude, archive_dir=None):
    """Load one archived product onto the model grid, as a complete daily calendar.

    Returns (dates, values, retrieved): the calendar from the first to the last
    archived day, an array (time, latitude, longitude) with NaN for days not
    held, and the download time of the version used for each day. For each day
    the version is the newest one downloaded before the forecast it first feeds
    was issued (see issue_cutoff), so inputs match what a live forecast had. Chlorophyll must already be
    on the model grid; sea temperature (°C) is copied from its coarser grid to
    the nearest cell within half a cell, as in step 02.
    """
    archive_dir = archive_dir or config.ARCHIVE_DIR
    all_versions = versions(source, archive_dir)
    if not all_versions:
        raise FileNotFoundError(f"No archived files for {source} in {archive_dir}")
    chosen = {}
    for date in sorted({v["date"] for v in all_versions}):
        day_versions = [v for v in all_versions if v["date"] == date]
        cutoff = issue_cutoff(source, date)
        in_time = [v for v in day_versions
                   if v["retrieved_utc"] and pd.Timestamp(v["retrieved_utc"]) <= cutoff]
        # The newest version available at issue time; if none was downloaded in
        # time (days saved later, e.g. by the first run), the first copy.
        chosen[date] = in_time[-1] if in_time else day_versions[0]
    files = [chosen[d]["path"] for d in sorted(chosen)]
    held = pd.DatetimeIndex([pd.Timestamp(d) for d in sorted(chosen)])
    dates = pd.date_range(held.min(), held.max(), freq="D")
    latitude = np.asarray(latitude)
    longitude = np.asarray(longitude)
    values = np.full((len(dates), len(latitude), len(longitude)), np.nan, dtype="float32")
    retrieved = {}
    variable = SOURCES[source]["variable"]

    for date, path in zip(sorted(chosen), files):
        with xr.open_dataset(path) as ds:
            field = ds[variable].isel(time=0).sortby("latitude").sortby("longitude").load()
            retrieved[date] = ds.attrs.get("retrieved_utc")
        if source == "sst":
            if field.attrs.get("units", "").lower() not in {"kelvin", "k"}:
                raise ValueError(f"Unexpected SST units in {path.name}: {field.attrs.get('units')}")
            field = field - 273.15
            for coord, target in [("latitude", latitude), ("longitude", longitude)]:
                spacing = float(np.median(np.abs(np.diff(field[coord].values))))
                field = field.reindex({coord: target}, method="nearest", tolerance=0.51 * spacing)
        else:
            for coord, target in [("latitude", latitude), ("longitude", longitude)]:
                if field.sizes[coord] != target.size or not np.allclose(field[coord].values, target, atol=1e-5, rtol=0):
                    raise ValueError(f"{path.name}: {coord} does not match the model grid")
        values[dates.get_loc(pd.Timestamp(date))] = field.values
    return dates, values, retrieved


def main():
    started = datetime.now(timezone.utc)
    print(f"Archive run started {started:%Y-%m-%d %H:%M:%S} UTC", flush=True)
    try:
        remote = open_sources()
        print(offered(remote).to_string(), flush=True)
        log = save_new_days(remote)
        saved = log[log["Status"] == "Saved"]
        revised = log[log["Status"].str.startswith("Revised")]
        print(f"Saved {len(saved)} new day(s): "
              + (", ".join(f"{r.Source} {r.Date}" for r in saved.itertuples()) or "none"), flush=True)
        if len(revised):
            print(f"Kept {len(revised)} later version(s): "
                  + ", ".join(f"{r.Source} {r.Date}" for r in revised.itertuples()), flush=True)
        print(holdings().to_string(), flush=True)
    except Exception as error:      # report clearly in the log, then fail
        print(f"Archive run FAILED: {error!r}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
