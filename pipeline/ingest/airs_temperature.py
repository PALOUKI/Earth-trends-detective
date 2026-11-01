"""Ingest the AIRS monthly standard surface-air-temperature field."""

from __future__ import annotations

import re
from pathlib import Path

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv
from pyhdf.SD import SD, SDC
from pyhdf.error import HDF4Error

SHORT_NAME = "AIRS3STM"
VERSION = "7.0"
FIELD = "SurfAirTemp_A"
RAW_DIR = Path("data/raw/airs3stm")
OUTPUT = Path("data/processed/airs_surface_air_temp.zarr")
FILENAME = re.compile(r"AIRS\.(\d{4})\.(\d{2})\.\d{2}\.L3\.RetStd_IR031\.v7\.0\..*\.hdf$")
FILL = -9999.0
TARGET_LAT = np.arange(-89.0, 90.0, 2.0)
TARGET_LON = np.arange(-179.0, 180.0, 2.0)


def _read(path: Path) -> tuple[pd.Timestamp, np.ndarray]:
    match = FILENAME.search(path.name)
    if not match:
        raise ValueError(f"Unexpected AIRS3STM v7 filename: {path.name}")
    timestamp = pd.Timestamp(year=int(match.group(1)), month=int(match.group(2)), day=1)
    source = SD(str(path), SDC.READ)
    try:
        field = source.select(FIELD)
        info = field.info()
        if info[2] != [180, 360]:
            raise ValueError(f"Unexpected AIRS SurfAirTemp_A grid in {path.name}: {info[2]}")
        raw = np.asarray(field.get(), dtype=np.float32)
        fill = float(field.attributes().get("_FillValue", FILL))
    finally:
        source.end()
    raw[(raw == fill) | (raw <= 0) | ~np.isfinite(raw)] = np.nan
    latitude = np.arange(-89.5, 90.0, 1.0)
    longitude = np.arange(-179.5, 180.0, 1.0)
    data = xr.DataArray(raw, dims=("lat", "lon"), coords={"lat": latitude, "lon": longitude})
    result = data.interp(lat=TARGET_LAT, lon=TARGET_LON, method="linear")
    return timestamp, np.asarray(result.values, dtype=np.float32)


def _valid(path: Path) -> bool:
    if not FILENAME.search(path.name):
        return False
    try:
        timestamp, values = _read(path)
        return (
            timestamp.month in range(1, 13)
            and values.shape == (90, 180)
            and np.isfinite(values).any()
        )
    except (HDF4Error, OSError, ValueError, KeyError):
        return False


def download_airs(
    start: str = "2002-09-01",
    end: str = "2012-08-31",
    raw_dir: Path = RAW_DIR,
) -> list[Path]:
    """Download ten years of monthly AIRS granules, verifying every HDF4 field."""
    load_dotenv()
    if not earthaccess.login(strategy="environment", persist=False):
        raise RuntimeError("Earthdata Login failed; check the local environment credentials.")
    granules = earthaccess.search_data(
        short_name=SHORT_NAME,
        version=VERSION,
        temporal=(start, end),
        count=250,
    )
    if not granules:
        raise RuntimeError(f"CMR returned no {SHORT_NAME} v{VERSION} granules for {start}–{end}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    for granule in granules:
        links = granule.data_links(access="https")
        if not links:
            raise RuntimeError(f"CMR supplied no HTTPS link for {granule['meta']['native-id']}")
        filename = Path(links[0].split("?", maxsplit=1)[0]).name
        path = raw_dir / filename
        if not _valid(path):
            if path.exists():
                path.replace(path.with_suffix(path.suffix + ".partial"))
            pending.append(granule)
    files = earthaccess.download(pending, str(raw_dir)) if pending else []
    completed = [Path(path) for path in files]
    bad = [path for path in completed if not _valid(path)]
    if bad:
        names = ", ".join(path.name for path in bad[:5])
        raise RuntimeError(f"AIRS download returned invalid HDF4 files: {names}")
    return completed


def prepare_airs(raw_dir: Path = RAW_DIR, output: Path = OUTPUT) -> Path:
    paths = sorted(path for path in raw_dir.glob("*.hdf") if _valid(path))
    if not paths:
        raise FileNotFoundError(f"No validated AIRS3STM v7 files under {raw_dir}")
    records = sorted((_read(path) for path in paths), key=lambda item: item[0])
    observed = pd.DatetimeIndex([item[0] for item in records])
    if observed.has_duplicates:
        raise ValueError("Duplicate AIRS monthly granules found")
    times = pd.date_range(observed[0], observed[-1], freq="MS")
    values = np.full((len(times), 90, 180), np.nan, dtype=np.float32)
    for timestamp, grid in records:
        values[times.get_loc(timestamp)] = grid
    n_valid = np.isfinite(values).sum(axis=0).astype(np.int16)
    keep = (n_valid >= 120) & (n_valid >= int(len(times) * 0.70))
    values[:, ~keep] = np.nan
    dataset = xr.Dataset(
        {
            "surface_air_temperature": (("time", "lat", "lon"), values),
            "n_valid": (("lat", "lon"), n_valid),
        },
        coords={"time": times, "lat": TARGET_LAT, "lon": TARGET_LON},
        attrs={
            "title": "NASA AIRS/Aqua monthly standard surface air temperature",
            "source": "NASA AIRS3STM version 7.0",
            "short_name": SHORT_NAME,
            "source_field": FIELD,
            "doi": "10.5067/UBENJB9D3T2H",
            "crs": "EPSG:4326",
            "processing": (
                "SurfAirTemp_A is interpolated from the verified 1 degree grid to "
                "2 degree centers; missing months are retained and cells require "
                "120 valid months and 70 percent coverage."
            ),
        },
    )
    dataset["surface_air_temperature"].attrs = {
        "long_name": "Monthly surface air temperature",
        "units": "K",
        "source_variable": FIELD,
        "unit_reference": "NASA AIRS V7 L3 Product User Guide",
    }
    dataset["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
    dataset = dataset.chunk({"time": -1, "lat": 30, "lon": 30})
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_zarr(output, mode="w", zarr_format=2)
    return output

