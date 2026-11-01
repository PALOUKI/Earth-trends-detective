"""Ingest NASA GPM IMERG monthly precipitation onto the analysis grid."""

from __future__ import annotations

import re
from pathlib import Path

import earthaccess
import h5py
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv

SHORT_NAME = "GPM_3IMERGM"
VERSION = "07"
DOI = "10.5067/GPM/IMERG/3B-MONTH/07"
RAW_DIR = Path("data/raw/gpm_3imergm")
OUTPUT = Path("data/processed/gpm_precipitation.zarr")
FIELD = "Grid/precipitation"
GRID_BLOCK = 20  # native grid is 0.1 degree; the analysis grid is 2 degrees.


def _coarsen_monthly_grid(
    raw: np.ndarray,
    *,
    fill_value: float,
    block_size: int = GRID_BLOCK,
) -> np.ndarray:
    """Mask source fill values and average valid source cells into 2-degree cells."""
    values = np.asarray(raw, dtype=np.float32)
    if values.ndim != 2 or values.shape[0] % block_size or values.shape[1] % block_size:
        raise ValueError(f"GPM grid shape {values.shape} is not divisible by {block_size}")
    valid = np.isfinite(values) & (values != fill_value) & (values > -9000)
    masked = np.where(valid, values, np.nan)
    height, width = values.shape
    blocks = masked.reshape(
        height // block_size, block_size, width // block_size, block_size
    )
    valid_blocks = np.isfinite(blocks)
    counts = valid_blocks.sum(axis=(1, 3))
    totals = np.nansum(blocks, axis=(1, 3))
    return np.divide(
        totals,
        counts,
        out=np.full(totals.shape, np.nan, dtype=np.float32),
        where=counts > 0,
    )


def _read_month(
    path: Path, *, block_size: int = GRID_BLOCK
) -> tuple[pd.Timestamp, np.ndarray, np.ndarray, np.ndarray]:
    """Read and verify one real GPM monthly granule and its file-level metadata."""
    with h5py.File(path, "r") as source:
        if FIELD not in source:
            raise ValueError(f"Expected {FIELD} in GPM granule {path.name}")
        dataset = source[FIELD]
        raw = np.asarray(dataset[0], dtype=np.float32).T
        attrs = dataset.attrs
        units = attrs.get("units", attrs.get("Units", b""))
        if isinstance(units, bytes):
            units = units.decode("ascii", errors="replace")
        if units != "mm/hr":
            raise ValueError(f"Unexpected GPM precipitation units in {path.name}: {units!r}")
        header = source.attrs.get("FileHeader", b"")
        if isinstance(header, bytes):
            header = header.decode("ascii", errors="replace")
        start = re.search(r"StartGranuleDateTime=(\d{4}-\d{2}-\d{2})T", header)
        interval = re.search(r"TimeInterval=([^;\n]+)", header)
        if (
            not start
            or not interval
            or interval.group(1).strip() != "MONTH"
            or f"DOI={DOI};" not in header
        ):
            raise ValueError(f"GPM granule is missing verified monthly time metadata: {path.name}")
        time = pd.Timestamp(start.group(1)).to_period("M").to_timestamp()
        lat = np.asarray(source["Grid/lat"][:], dtype=np.float64)
        lon = np.asarray(source["Grid/lon"][:], dtype=np.float64)
        fill_value = float(attrs.get("_FillValue", -9999.9))
    if raw.shape != (lat.size, lon.size):
        raise ValueError(f"GPM coordinate dimensions do not match precipitation in {path.name}")
    order_lat = np.argsort(lat)
    order_lon = np.argsort(lon)
    grid = _coarsen_monthly_grid(
        raw[order_lat][:, order_lon], fill_value=fill_value, block_size=block_size
    )
    return time, grid, lat[order_lat], lon[order_lon]


def _is_complete_granule(path: Path) -> bool:
    """Check that a cached monthly file has the full readable precipitation array."""
    try:
        with h5py.File(path, "r") as source:
            dataset = source[FIELD]
            header = source.attrs.get("FileHeader", b"")
            if isinstance(header, bytes):
                header = header.decode("ascii", errors="replace")
            units = dataset.attrs.get("units", dataset.attrs.get("Units", b""))
            if isinstance(units, bytes):
                units = units.decode("ascii", errors="replace")
            if dataset.shape != (1, 3600, 1800) or units != "mm/hr":
                return False
            if f"DOI={DOI};" not in header or "TimeInterval=MONTH" not in header:
                return False
            # Force HDF5 to read the entire compressed payload; partial files can open
            # and expose metadata while failing only when the last chunks are accessed.
            dataset[:]
        return True
    except (OSError, KeyError, ValueError):
        return False


def download_gpm(
    start: str = "2000-01-01", end: str = "2025-09-30", raw_dir: Path = RAW_DIR
) -> list[Path]:
    """Search CMR and download the exact GPM short_name/version range."""
    load_dotenv()
    if not earthaccess.login(strategy="environment", persist=False):
        raise RuntimeError("Earthdata Login failed; check the local environment credentials.")
    granules = earthaccess.search_data(
        short_name=SHORT_NAME,
        version=VERSION,
        temporal=(start, end),
        count=1000,
    )
    if not granules:
        raise RuntimeError(f"CMR returned no {SHORT_NAME} v{VERSION} granules for {start}–{end}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    for granule in granules:
        links = granule.data_links(access="https")
        if not links:
            raise RuntimeError(
                f"CMR supplied no HTTPS data link for {granule['meta']['native-id']}"
            )
        destination = raw_dir / Path(links[0].split("?", maxsplit=1)[0]).name
        if not _is_complete_granule(destination):
            if destination.exists():
                destination.replace(destination.with_suffix(destination.suffix + ".partial"))
            pending.append(granule)
    files = earthaccess.download(pending, str(raw_dir)) if pending else []
    completed = [Path(path) for path in files]
    bad_files = [path for path in completed if not _is_complete_granule(path)]
    if bad_files:
        names = ", ".join(path.name for path in bad_files[:5])
        raise RuntimeError(f"GPM download produced incomplete or invalid HDF5 files: {names}")
    return completed


def prepare_gpm(raw_dir: Path = RAW_DIR, output: Path = OUTPUT) -> Path:
    """Normalize verified monthly granules to a regular 2-degree monthly Zarr."""
    records = [_read_month(path) for path in sorted(raw_dir.glob("*.HDF5"))]
    if not records:
        raise FileNotFoundError(f"No downloaded GPM monthly granules under {raw_dir}")
    records.sort(key=lambda record: record[0])
    observed_times = pd.DatetimeIndex([record[0] for record in records])
    if observed_times.has_duplicates:
        raise ValueError("GPM source contains duplicate monthly granules")
    lat, lon = records[0][2:]
    expected_shape = (lat.size // GRID_BLOCK, lon.size // GRID_BLOCK)
    if any(record[1].shape != expected_shape for record in records):
        raise ValueError("GPM granules do not share one consistent global analysis grid")
    times = pd.date_range(observed_times[0], observed_times[-1], freq="MS")
    data = np.full((times.size, *expected_shape), np.nan, dtype=np.float32)
    for month, grid, _, _ in records:
        data[times.get_loc(month)] = grid
    n_valid = np.isfinite(data).sum(axis=0).astype(np.int16)
    valid = (n_valid >= max(120, int(len(records) * 0.70)))
    data[:, ~valid] = np.nan
    lat2 = lat.reshape(-1, GRID_BLOCK).mean(axis=1)
    lon2 = lon.reshape(-1, GRID_BLOCK).mean(axis=1)
    dataset = xr.Dataset(
        {
            "precipitation_rate": (("time", "lat", "lon"), data),
            "n_valid": (("lat", "lon"), n_valid),
        },
        coords={"time": times, "lat": lat2, "lon": lon2},
        attrs={
            "title": "NASA GPM IMERG Final Monthly precipitation rate",
            "source": "NASA GPM_3IMERGM version 07",
            "doi": DOI,
            "source_short_name": SHORT_NAME,
            "source_field": FIELD,
            "crs": "EPSG:4326",
            "grid": "0.1 degree source averaged to regular 2 degree cells",
            "processing": (
                "Monthly granule precipitation cells are averaged within 2 degree blocks; "
                "fill values are excluded and cells require at least 120 valid months and "
                "70 percent temporal coverage."
            ),
        },
    )
    dataset["precipitation_rate"].attrs = {
        "long_name": "Monthly mean precipitation rate",
        "units": "mm/hr",
        "source_variable": FIELD,
    }
    dataset["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
    dataset = dataset.chunk({"time": -1, "lat": 30, "lon": 30})
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_zarr(output, mode="w", zarr_format=2)
    return output


def ingest() -> Path:
    download_gpm()
    return prepare_gpm()
