"""Ingest NASA Aura OMI daily tropospheric NO2 and form monthly means."""

from __future__ import annotations

import re
from pathlib import Path

import earthaccess
import h5py
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv

SHORT_NAME = "OMNO2d"
VERSION = "004"
DOI = "10.5067/AURA/OMI/DATA3407"
FIELD = "HDFEOS/GRIDS/ColumnAmountNO2/Data Fields/ColumnAmountNO2TropCloudScreened"
STRUCT_METADATA = "HDFEOS INFORMATION/StructMetadata.0"
SOURCE_SHAPE = (720, 1440)  # global 0.25-degree grid from the HDF-EOS structure metadata.
GRID_BLOCK = 8  # native grid aggregated to the regular 2-degree analysis grid.
RAW_DIR = Path("data/raw/omi_omno2d")
OUTPUT = Path("data/processed/omi_no2.zarr")
DEFAULT_START = "2005-01-01"
DEFAULT_END = "2014-12-31"
FILL_VALUE = -1.2676506e30


def _valid_grid_metadata(source: h5py.File) -> bool:
    """Verify the source grid dimensions, geographic bounds, and pixel registration."""
    if STRUCT_METADATA not in source:
        return False
    metadata = source[STRUCT_METADATA][()]
    if isinstance(metadata, bytes):
        metadata = metadata.decode("ascii", errors="replace")
    required = (
        "XDim=1440",
        "YDim=720",
        "UpperLeftPointMtrs=(-180000000.000000,-90000000.000000)",
        "LowerRightMtrs=(180000000.000000,90000000.000000)",
        "PixelRegistration=HE5_HDFE_CENTER",
        "Projection=HE5_GCTP_GEO",
    )
    return all(value in metadata for value in required)


def _coarsen_daily_grid(raw: np.ndarray, *, block_size: int = GRID_BLOCK) -> np.ndarray:
    """Mask OMI fill pixels and average the valid 0.25-degree values to 2 degrees."""
    values = np.asarray(raw, dtype=np.float32)
    if values.shape != SOURCE_SHAPE:
        raise ValueError(f"Unexpected OMNO2d grid shape: {values.shape}")
    valid = np.isfinite(values) & (values > -1e20)
    blocks = np.where(valid, values, np.nan).reshape(
        SOURCE_SHAPE[0] // block_size,
        block_size,
        SOURCE_SHAPE[1] // block_size,
        block_size,
    )
    counts = np.isfinite(blocks).sum(axis=(1, 3))
    totals = np.nansum(blocks, axis=(1, 3))
    return np.divide(
        totals,
        counts,
        out=np.full(totals.shape, np.nan, dtype=np.float32),
        where=counts > 0,
    )


def _read_daily(path: Path) -> tuple[pd.Timestamp, np.ndarray]:
    """Read a version-004 OMI daily grid with exact file-level units."""
    match = re.search(r"OMNO2d_(\d{4})m(\d{2})(\d{2})_v004-", path.name)
    if not match:
        raise ValueError(f"File name does not identify an OMNO2d v004 daily granule: {path.name}")
    with h5py.File(path, "r") as source:
        if FIELD not in source:
            raise ValueError(f"Expected cloud-screened tropospheric NO2 field in {path.name}")
        dataset = source[FIELD]
        if dataset.shape != SOURCE_SHAPE:
            raise ValueError(f"Unexpected OMNO2d grid shape in {path.name}: {dataset.shape}")
        if not _valid_grid_metadata(source):
            raise ValueError(f"Unexpected OMNO2d geographic grid metadata in {path.name}")
        units = dataset.attrs.get("Units", dataset.attrs.get("units", b""))
        if isinstance(units, bytes):
            units = units.decode("ascii", errors="replace")
        if units != "molec/cm2":
            raise ValueError(f"Unexpected OMNO2d units in {path.name}: {units!r}")
        raw = np.asarray(dataset[:], dtype=np.float32)
        fill = float(np.asarray(dataset.attrs.get("_FillValue", FILL_VALUE)).reshape(-1)[0])
    raw[(raw == fill) | (raw <= -1e20) | ~np.isfinite(raw)] = np.nan
    return pd.Timestamp("-".join(match.groups())), _coarsen_daily_grid(raw)


def _is_complete_daily(path: Path) -> bool:
    """Check cached OMI files by reading the full cloud-screened data field."""
    if not re.search(r"OMNO2d_\d{4}m\d{4}_v004-.*\.he5$", path.name):
        return False
    try:
        with h5py.File(path, "r") as source:
            dataset = source[FIELD]
            units = dataset.attrs.get("Units", dataset.attrs.get("units", b""))
            if isinstance(units, bytes):
                units = units.decode("ascii", errors="replace")
            if dataset.shape != SOURCE_SHAPE or units != "molec/cm2":
                return False
            if not _valid_grid_metadata(source):
                return False
            dataset[:]
        return True
    except (OSError, KeyError, ValueError):
        return False


def download_omi(
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
    raw_dir: Path = RAW_DIR,
) -> list[Path]:
    """Download real CMR daily granules to aggregate to monthly values."""
    load_dotenv()
    if not earthaccess.login(strategy="environment", persist=False):
        raise RuntimeError("Earthdata Login failed; check the local environment credentials.")
    granules = earthaccess.search_data(
        short_name=SHORT_NAME,
        version=VERSION,
        temporal=(start, end),
        count=5000,
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
        filename = Path(links[0].split("?", maxsplit=1)[0]).name
        destination = raw_dir / filename
        if not _is_complete_daily(destination):
            if destination.exists():
                destination.replace(destination.with_suffix(destination.suffix + ".partial"))
            pending.append(granule)
    files = earthaccess.download(pending, str(raw_dir)) if pending else []
    completed = [Path(path) for path in files]
    bad_files = [path for path in completed if not _is_complete_daily(path)]
    if bad_files:
        names = ", ".join(path.name for path in bad_files[:5])
        raise RuntimeError(f"OMI download produced incomplete or invalid files: {names}")
    return completed


def prepare_omi(raw_dir: Path = RAW_DIR, output: Path = OUTPUT) -> Path:
    """Aggregate daily OMI grids to monthly means and write a 2-degree Zarr."""
    paths = sorted(raw_dir.glob("*OMNO2d_*_v004-*.he5"))
    if not paths:
        raise FileNotFoundError(f"No downloaded OMNO2d v004 files under {raw_dir}")
    monthly_sums: dict[pd.Timestamp, np.ndarray] = {}
    monthly_counts: dict[pd.Timestamp, np.ndarray] = {}
    for path in paths:
        day, grid = _read_daily(path)
        month = day.to_period("M").to_timestamp()
        if month not in monthly_sums:
            monthly_sums[month] = np.zeros(grid.shape, dtype=np.float64)
            monthly_counts[month] = np.zeros(grid.shape, dtype=np.uint16)
        valid = np.isfinite(grid)
        monthly_sums[month][valid] += grid[valid]
        monthly_counts[month][valid] += 1
    observed_months = pd.DatetimeIndex(sorted(monthly_sums))
    times = pd.date_range(observed_months[0], observed_months[-1], freq="MS")
    monthly = np.full((times.size, 90, 180), np.nan, dtype=np.float32)
    for month, index in zip(observed_months, times.get_indexer(observed_months), strict=True):
        counts = monthly_counts[month]
        monthly[index] = np.divide(
            monthly_sums[month],
            counts,
            out=np.full((90, 180), np.nan, dtype=np.float32),
            where=counts > 0,
        )
    n_valid = np.isfinite(monthly).sum(axis=0).astype(np.int16)
    enough_data = (n_valid >= 120) & (n_valid >= int(times.size * 0.70))
    monthly[:, ~enough_data] = np.nan
    lat = -89.0 + 2.0 * np.arange(90)
    lon = -179.0 + 2.0 * np.arange(180)
    dataset = xr.Dataset(
        {
            "no2_tropospheric_column": (("time", "lat", "lon"), monthly),
            "n_valid": (("lat", "lon"), n_valid),
        },
        coords={"time": times, "lat": lat, "lon": lon},
        attrs={
            "title": "NASA Aura OMI daily tropospheric NO2 Level-3 monthly means",
            "source": "NASA Aura OMI OMNO2d version 004",
            "doi": DOI,
            "source_short_name": SHORT_NAME,
            "source_field": FIELD,
            "crs": "EPSG:4326",
            "grid": "0.25 degree source averaged to regular 2 degree cells",
            "processing": (
                "Cloud-screened daily tropospheric NO2 grid cells were averaged spatially "
                "to 2 degrees, then valid daily values were averaged per calendar month. "
                "Missing monthly cells were retained as NaN; cells require 120 valid months "
                "and 70 percent temporal coverage."
            ),
        },
    )
    dataset["no2_tropospheric_column"].attrs = {
        "long_name": "Monthly mean cloud-screened tropospheric NO2 column",
        "units": "molec/cm2",
        "source_variable": FIELD,
    }
    dataset["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
    dataset = dataset.chunk({"time": -1, "lat": 30, "lon": 30})
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_zarr(output, mode="w", zarr_format=2)
    return output


def ingest() -> Path:
    download_omi()
    return prepare_omi()
