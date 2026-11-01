"""Ingest the NASA MODIS Terra monthly global vegetation-index product.

The source is MOD13C2 v061 (CMG 0.05 degree), served by NASA LP DAAC.
Native NDVI/EVI integers are scaled by 1/10000. Pixels with reliability ranks
above 1 and fill/out-of-range values are excluded before aggregation to 2°.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr
from pyhdf.SD import SD, SDC

SHORT_NAME = "MOD13C2"
VERSION = "061"
DOI = "10.5067/MODIS/MOD13C2.061"
SOURCE_VARIABLE = "CMG 0.05 Deg Monthly NDVI"
SOURCE_QUALITY = "CMG 0.05 Deg Monthly pixel reliability"
RAW_DIR = Path("data/raw/modis/mod13c2")
START = "2000-02-01"


def _coarsen_hdf(path: Path, variable: str) -> np.ndarray:
    """Read one granule and aggregate valid 0.05° values to a 2° grid."""
    if variable not in {"ndvi", "evi"}:
        raise ValueError("MODIS vegetation variable must be 'ndvi' or 'evi'")
    source_name = SOURCE_VARIABLE if variable == "ndvi" else "CMG 0.05 Deg Monthly EVI"
    source = SD(str(path), SDC.READ)
    try:
        raw = np.asarray(source.select(source_name).get(), dtype=np.int16)
        quality = np.asarray(source.select(SOURCE_QUALITY).get(), dtype=np.int16)
        attrs = source.select(source_name).attributes()
    finally:
        source.end()
    if raw.shape != (3600, 7200) or quality.shape != raw.shape:
        raise ValueError(f"Unexpected MOD13C2 global grid shape: {raw.shape}")
    return _aggregate_arrays(
        raw,
        quality,
        fill_value=attrs["_FillValue"],
        valid_range=tuple(attrs["valid_range"]),
        scale_factor=attrs["scale_factor"],
    )


def _aggregate_arrays(
    raw: np.ndarray,
    quality: np.ndarray,
    *,
    fill_value: int,
    valid_range: tuple[int, int],
    scale_factor: float,
) -> np.ndarray:
    """Apply MODIS fill, range, QA, and scale metadata before block averaging."""
    if raw.ndim != 2 or raw.shape != quality.shape or any(size % 40 for size in raw.shape):
        raise ValueError("MODIS arrays must be same-shaped 2D arrays divisible into 40-cell blocks")
    valid = (raw >= valid_range[0]) & (raw <= valid_range[1]) & (raw != fill_value)
    valid &= (quality == 0) | (quality == 1)
    values = np.where(valid, raw.astype(np.float32) / scale_factor, np.nan)
    rows, cols = raw.shape[0] // 40, raw.shape[1] // 40
    blocks = values.reshape(rows, 40, cols, 40)
    counts = np.isfinite(blocks).sum(axis=(1, 3))
    sums = np.nansum(blocks, axis=(1, 3))
    coarse = np.full((rows, cols), np.nan, dtype=np.float32)
    np.divide(sums, counts, out=coarse, where=counts > 0)
    return coarse


def prepare_modis(
    raw_dir: Path = RAW_DIR,
    output: Path | None = None,
    variable: str = "ndvi",
) -> Path:
    """Normalize all cached monthly MOD13C2 HDF granules into chunked Zarr."""
    if variable not in {"ndvi", "evi"}:
        raise ValueError("MODIS vegetation variable must be 'ndvi' or 'evi'")
    output = output or Path(f"data/processed/modis_{variable}.zarr")
    files = sorted(raw_dir.glob("MOD13C2.A*.061.*.hdf"))
    if len(files) < 120:
        raise ValueError(
            "At least 120 monthly MOD13C2 granules are required for trend analysis; "
            f"found {len(files)}."
        )
    values: list[np.ndarray] = []
    dates: list[pd.Timestamp] = []
    for path in files:
        acquisition = path.name.split(".")[1]
        dates.append(pd.to_datetime(datetime.strptime(acquisition[1:], "%Y%j")))
        values.append(_coarsen_hdf(path, variable))
    if len(set(dates)) != len(dates):
        raise ValueError("Duplicate MOD13C2 monthly granules were found")
    if dates != sorted(dates):
        raise ValueError("MOD13C2 granules must be in chronological order")
    expected = pd.date_range(dates[0], dates[-1], freq="MS")
    if len(expected) != len(dates) or list(expected) != dates:
        raise ValueError("MOD13C2 monthly granules must form an uninterrupted monthly series")
    data = np.stack(values)
    lat = np.arange(89.0, -90.0, -2.0)
    lon = np.arange(-179.0, 180.0, 2.0)
    order = np.argsort(lat)
    name = f"{variable}_index"
    ds = xr.Dataset(
        {
            name: (("time", "lat", "lon"), data[:, order, :]),
            "n_valid": (
                ("lat", "lon"),
                np.isfinite(data[:, order, :]).sum(axis=0).astype(np.int16),
            ),
        },
        coords={"time": pd.DatetimeIndex(dates), "lat": lat[order], "lon": lon},
        attrs={
            "title": f"NASA MODIS Terra monthly {variable.upper()} vegetation index",
            "source": "NASA LP DAAC MOD13C2 Version 061",
            "short_name": SHORT_NAME,
            "version": VERSION,
            "doi": DOI,
            "source_variable": (
                SOURCE_VARIABLE if variable == "ndvi" else "CMG 0.05 Deg Monthly EVI"
            ),
            "source_quality_variable": SOURCE_QUALITY,
            "crs": "EPSG:4326",
            "grid": (
                "2 degree aggregation of global 0.05 degree CMG; "
                "reliability ranks 0 and 1 only"
            ),
            "processing": (
                "Scale factor 1/10000; fill and invalid values masked; "
                "monthly values averaged spatially."
            ),
        },
    )
    ds[name].attrs = {
        "long_name": f"Monthly {variable.upper()} vegetation index",
        "units": "1",
        "scale_factor_applied": 0.0001,
        "seasonal_adjustment": "Removed during regional trend analysis.",
    }
    ds["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
    ds = ds.chunk({"time": -1, "lat": 30, "lon": 30})
    output.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(output, mode="w", zarr_format=2)
    return output


def download_modis(
    start: str = START,
    end: str | None = None,
    raw_dir: Path = RAW_DIR,
) -> list[Path]:
    """Download actual LP DAAC monthly global granules for the requested period."""
    auth = earthaccess.login(strategy="environment", persist=False)
    if not auth:
        raise RuntimeError(
            "Earthdata authentication failed; configure EARTHDATA_USERNAME/PASSWORD."
        )
    end = end or pd.Timestamp.utcnow().strftime("%Y-%m-%d")
    granules = earthaccess.search_data(
        short_name=SHORT_NAME,
        version=VERSION,
        temporal=(start, end),
        count=500,
    )
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = {path.name for path in raw_dir.glob("MOD13C2.A*.061.*.hdf")}
    missing = [item for item in granules if item["meta"]["native-id"] not in existing]
    return [Path(path) for path in earthaccess.download(missing, str(raw_dir))] if missing else []
