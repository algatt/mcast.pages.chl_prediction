"""The daily near-real-time archive (step 08).

Saves every day the live Copernicus feed offers that is not already saved,
one file per day per product, and never overwrites. Wind (both ASCAT passes)
is archived for later use (step 12 found that wind events come before sudden
changes); no forecast uses it yet. Used by
08-NRT-Archive.ipynb and by the scheduled job:

    cd experiment_v2 && .venv/bin/python -m chlforecast.archive
"""

import sys
import time
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import xarray as xr

from . import config

SOURCES = {
    "chl": {
        "dataset_id": "cmems_obs-oc_med_bgc-plankton_nrt_l3-multi-1km_P1D",
        "version": "202611",
        "variable": "CHL",
        "margin": 0.0,
        "recent_days": None,  # keep every day the rolling window offers
        "lag_days": config.CHL_LAG_DAYS,
    },
    "chl_l4": {
        "dataset_id": "cmems_obs-oc_med_bgc-plankton_nrt_l4-gapfree-multi-1km_P1D",
        "variable": "CHL",
        "version": "202611",
        "margin": 0.0,
        "recent_days": None,
        "lag_days": config.CHL_LAG_DAYS,
    },
    "sst": {
        "dataset_id": "SST_MED_SST_L3S_NRT_OBSERVATIONS_010_012_a",
        "version": "202311",
        "variable": "adjusted_sea_surface_temperature",
        "margin": 0.07,  # covers the edge SST cells, as in step 07
        "recent_days": 30,  # the SST record goes back to 2008
        "lag_days": config.SST_LAG_DAYS,
    },
    # ASCAT wind from Metop-B, the satellite of the training data (step 01), one
    # source per pass. The live feed keeps its whole record, so 30 days suffice.
    "wind_asc": {
        "dataset_id": "cmems_obs-wind_glo_phy_nrt_l3-metopb-ascat-asc-0.125deg_P1D-i",
        "version": "202611",
        # The first variable is the one counted as "valid pixels" in the log.
        "variables": [
            "wind_speed",
            "eastward_wind",
            "northward_wind",
            "measurement_time",
            "wvc_quality_flag",
        ],
        "margin": 0.07,  # covers the edge cells of the 0.125° grid
        "recent_days": 30,
        "lag_days": config.WIND_LAG_DAYS,
    },
    "wind_des": {
        "dataset_id": "cmems_obs-wind_glo_phy_nrt_l3-metopb-ascat-des-0.125deg_P1D-i",
        "version": "202611",
        "variables": [
            "wind_speed",
            "eastward_wind",
            "northward_wind",
            "measurement_time",
            "wvc_quality_flag",
        ],
        "margin": 0.07,
        "recent_days": 30,
        "lag_days": config.WIND_LAG_DAYS,
    },
}


def variables_of(source):
    """The variables archived for a source (one for most, several for wind)."""
    return source.get("variables") or [source["variable"]]


def open_sources(source_names=None):
    """Open each live dataset (lazily; no data is downloaded yet)."""
    import copernicusmarine

    remote = {}
    for name in SOURCES if source_names is None else source_names:
        source = SOURCES[name]
        catalogue = copernicusmarine.describe(dataset_id=source["dataset_id"])
        dataset = next(
            d
            for product in catalogue.products
            for d in product.datasets
            if d.dataset_id == source["dataset_id"]
        )
        offered_versions = {v.label: v for v in dataset.versions}
        version = source["version"]
        if version not in offered_versions:
            raise RuntimeError(
                f"{name}: pinned version {version} is no longer offered "
                f"(offered: {sorted(offered_versions)}). Compare the new version, "
                "then update SOURCES."
            )
        newer = sorted(set(offered_versions) - {version})
        if newer:
            print(
                f"NOTE {name}: other version(s) offered {newer}; still using {version}",
                flush=True,
            )
        retires = [
            p.retired_date for p in offered_versions[version].parts if p.retired_date
        ]
        if retires:
            print(f"NOTE {name}: version {version} retires {min(retires)}", flush=True)

        data = copernicusmarine.open_dataset(
            dataset_id=source["dataset_id"],
            dataset_version=version,
            variables=variables_of(source),
            minimum_longitude=config.REGION["minimum_longitude"] - source["margin"],
            maximum_longitude=config.REGION["maximum_longitude"] + source["margin"],
            minimum_latitude=config.REGION["minimum_latitude"] - source["margin"],
            maximum_latitude=config.REGION["maximum_latitude"] + source["margin"],
        )
        data = data.rename(
            {
                old: new
                for old, new in [("lat", "latitude"), ("lon", "longitude")]
                if old in data.coords and new not in data.coords
            }
        )
        remote[name] = {"data": data, "version": version}
    return remote


def offered(remote):
    """What each live dataset currently offers."""
    rows = []
    for name, r in remote.items():
        times = pd.DatetimeIndex(r["data"].time.values)
        rows.append(
            {
                "Source": name,
                "Version": r["version"],
                "Days offered": len(times),
                "First": f"{times.min():%Y-%m-%d}",
                "Latest": f"{times.max():%Y-%m-%d}",
            }
        )
    return pd.DataFrame(rows).set_index("Source")


def save_new_days(remote, archive_dir=None):
    """Save every offered day not yet in the archive. Returns the log rows."""
    archive_dir = archive_dir or config.ARCHIVE_DIR
    rows = []

    for name, opened in remote.items():
        source = SOURCES[name]
        data = opened["data"]
        names = variables_of(source)
        days = pd.DatetimeIndex(data.time.values)
        if source["recent_days"]:
            newest = days.max().normalize()
            days = days[days >= newest - pd.Timedelta(days=source["recent_days"] - 1)]

        out_dir = archive_dir / name
        out_dir.mkdir(parents=True, exist_ok=True)

        for day in days:
            path = out_dir / f"{day:%Y-%m-%d}.nc"
            row = {"Source": name, "Date": f"{day:%Y-%m-%d}"}

            field = data[names].sel(time=[day]).load()
            retrieved_utc = pd.Timestamp.now(tz="UTC")
            row["Retrieved (UTC)"] = retrieved_utc.isoformat()
            valid = int(np.isfinite(field[names[0]]).sum().item())

            # The first copy is never overwritten. If the live feed now offers
            # different values for the day (an early file completed later, or a
            # reprocessing), that version is kept too, under revisions/.
            if path.exists():
                if _same_values(path, field, names) or _same_as_a_revision(
                    out_dir, day, field, names
                ):
                    rows.append({**row, "Status": "Already archived"})
                    continue
                stamp = retrieved_utc.strftime("%Y%m%dT%H%M%SZ")
                path = out_dir / "revisions" / f"{day:%Y-%m-%d}_{stamp}.nc"
                path.parent.mkdir(exist_ok=True)
                row["Status"] = "Revised: new version kept"
            field.attrs.update(
                {
                    "source_dataset_id": source["dataset_id"],
                    "source_dataset_version": opened["version"],
                    "retrieved_utc": retrieved_utc.isoformat(),
                    "archive_note": "First retrieved copy; never overwritten",
                }
            )
            for v in field.variables:
                field[v].encoding = {}

            # Write under a temporary name first, so an interrupted run never
            # leaves a half-written file that looks complete.
            partial = path.with_name(path.name + ".part")
            field.to_netcdf(
                partial, encoding={v: {"zlib": True, "complevel": 4} for v in names}
            )
            partial.rename(path)
            rows.append({"Status": "Saved", **row, "Valid pixels": valid})

    log = pd.DataFrame(rows)
    # Fixed column order: the log file is appended to on every run.
    log = log.reindex(
        columns=["Source", "Date", "Status", "Valid pixels", "Retrieved (UTC)"]
    )
    log_path = archive_dir / "archive_log.csv"
    log.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
    return log


def _same_values(path, field, names):
    with xr.open_dataset(path) as stored:
        return all(
            np.array_equal(stored[v].values, field[v].values, equal_nan=True)
            for v in names
        )


def _same_as_a_revision(out_dir, day, field, names):
    return any(
        _same_values(p, field, names)
        for p in sorted((out_dir / "revisions").glob(f"{day:%Y-%m-%d}_*.nc"))
    )


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
            out.append(
                {
                    "date": date,
                    "retrieved_utc": ds.attrs.get("retrieved_utc"),
                    "version": ds.attrs.get("source_dataset_version"),
                    "path": path,
                }
            )
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
        rows.append(
            {
                "Source": name,
                "Days archived": len(dates),
                "Later versions kept": revised,
                "First": f"{dates.min():%Y-%m-%d}",
                "Last": f"{dates.max():%Y-%m-%d}",
                "Missing days": ", ".join(f"{d:%Y-%m-%d}" for d in missing) or "None",
            }
        )
    return pd.DataFrame(rows).set_index("Source")


def load(
    source,
    latitude,
    longitude,
    archive_dir=None,
    *,
    as_of=None,
    manifest=None,
    version=None,
):
    """Load an archived source onto the model grid and return dates, values, retrieved.

    With as_of, use the newest copy retrieved by that UTC timestamp, subject
    to the source's observation lag. Unavailable days remain NaN.
    Without as_of, use the existing retrospective selection rules.
    """
    archive_dir = archive_dir or config.ARCHIVE_DIR
    all_versions = versions(source, archive_dir)
    if version is not None:
        all_versions = [v for v in all_versions if v["version"] == version]
    if not all_versions:
        raise FileNotFoundError(f"No archived files for {source} in {archive_dir}")

    cutoff = None if as_of is None else pd.to_datetime(as_of, utc=True)
    held_days = sorted({v["date"] for v in all_versions})
    dates = pd.date_range(held_days[0], held_days[-1], freq="D")
    chosen = {}

    for date in held_days:
        day_versions = [v for v in all_versions if v["date"] == date]

        if cutoff is None:
            deadline = issue_cutoff(source, date)
        else:
            earliest_day = pd.Timestamp(date, tz="UTC") + pd.Timedelta(
                days=SOURCES[source]["lag_days"]
            )
            if earliest_day > cutoff:
                continue
            deadline = cutoff

        in_time = [
            v
            for v in day_versions
            if v["retrieved_utc"] and pd.Timestamp(v["retrieved_utc"]) <= deadline
        ]

        if in_time:
            chosen[date] = max(in_time, key=lambda v: pd.Timestamp(v["retrieved_utc"]))
        elif cutoff is None:
            chosen[date] = day_versions[0]

    files = [chosen[d]["path"] for d in sorted(chosen)]
    latitude = np.asarray(latitude)
    longitude = np.asarray(longitude)
    values = np.full(
        (len(dates), len(latitude), len(longitude)), np.nan, dtype="float32"
    )
    retrieved = {}
    if "variable" not in SOURCES[source]:
        raise NotImplementedError(
            f"{source} is archived for later use; loading it onto the model grid is not written yet"
        )
    variable = SOURCES[source]["variable"]

    for date, path in zip(sorted(chosen), files):
        with xr.open_dataset(path) as ds:
            field = (
                ds[variable].isel(time=0).sortby("latitude").sortby("longitude").load()
            )
            retrieved[date] = ds.attrs.get("retrieved_utc")
            if manifest is not None:
                manifest.append(
                    {
                        "source": source,
                        "observation_date": date,
                        "dataset_version": ds.attrs.get("source_dataset_version"),
                        "retrieved_utc": retrieved[date],
                        "archive_file": path.relative_to(archive_dir).as_posix(),
                    }
                )
        if source == "sst":
            if field.attrs.get("units", "").lower() not in {"kelvin", "k"}:
                raise ValueError(
                    f"Unexpected SST units in {path.name}: {field.attrs.get('units')}"
                )
            field = field - 273.15
            for coord, target in [("latitude", latitude), ("longitude", longitude)]:
                spacing = float(np.median(np.abs(np.diff(field[coord].values))))
                field = field.reindex(
                    {coord: target}, method="nearest", tolerance=0.51 * spacing
                )
        else:
            for coord, target in [("latitude", latitude), ("longitude", longitude)]:
                if field.sizes[coord] != target.size or not np.allclose(
                    field[coord].values, target, atol=1e-5, rtol=0
                ):
                    raise ValueError(
                        f"{path.name}: {coord} does not match the model grid"
                    )
        values[dates.get_loc(pd.Timestamp(date))] = field.values
    return dates, values, retrieved


ATTEMPTS = 3
RETRY_WAIT_S = 300


def main():
    started = datetime.now(UTC)
    print(f"Archive run started {started:%Y-%m-%d %H:%M:%S} UTC", flush=True)
    pending = list(SOURCES)

    for attempt in range(1, ATTEMPTS + 1):
        failed = []

        for name in pending:
            try:
                remote = open_sources([name])
                print(offered(remote).to_string(), flush=True)
                log = save_new_days(remote)
            except Exception as error:
                failed.append(name)
                print(
                    f"{name} FAILED (attempt {attempt}/{ATTEMPTS}): {error!r}",
                    flush=True,
                )
                continue

            saved = log.loc[log["Status"] == "Saved", "Date"]
            revised = log.loc[log["Status"].str.startswith("Revised"), "Date"]
            print(
                f"Saved {len(saved)} new day(s) for {name}: {', '.join(saved) or 'none'}",
                flush=True,
            )
            if len(revised):
                print(
                    f"Kept {len(revised)} revision(s) for {name}: {', '.join(revised)}",
                    flush=True,
                )

        pending = failed
        if not pending:
            break
        if attempt < ATTEMPTS:
            time.sleep(RETRY_WAIT_S)

    if pending:
        print(f"Archive run FAILED for: {', '.join(pending)}", flush=True)
        return 1

    print(holdings().to_string(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
