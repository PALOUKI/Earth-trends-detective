"""Ingest the NASA MODIS Terra monthly global vegetation-index product.

The source is MOD13C2 v061 (CMG 0.05 degree), served by NASA LP DAAC.
Native NDVI/EVI integers are scaled by 1/10000. Pixels with reliability ranks
above 1 and fill/out-of-range values are excluded before aggregation to 2°.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import earthaccess
import numpy as np
import pandas as pd
import requests
import xarray as xr
from dotenv import load_dotenv
from pyhdf.error import HDF4Error
from pyhdf.SD import SD, SDC

SHORT_NAME = "MOD13C2"
VERSION = "061"
DOI = "10.5067/MODIS/MOD13C2.061"
SOURCE_VARIABLE = "CMG 0.05 Deg Monthly NDVI"
SOURCE_QUALITY = "CMG 0.05 Deg Monthly pixel reliability"
RAW_DIR = Path("data/raw/modis/mod13c2")
START = "2000-02-01"
DOWNLOAD_WORKERS = 3
DOWNLOAD_ATTEMPTS = 8


def _coarsen_hdf(path: Path, variable: str) -> np.ndarray:
    """Read one granule and aggregate valid 0.05° values to a 2° grid."""
    if variable not in {"ndvi", "evi"}:
        raise ValueError("MODIS vegetation variable must be 'ndvi' or 'evi'")
    source_name = SOURCE_VARIABLE if variable == "ndvi" else "CMG 0.05 Deg Monthly EVI"
    try:
        source = SD(str(path), SDC.READ)
    except HDF4Error as error:
        raise ValueError(f"Unreadable or incomplete MOD13C2 HDF granule: {path.name}") from error
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


def _valid_granule(path: Path, *, read_pixels: bool = False) -> bool:
    """Check the HDF4 directory and declared global arrays without loading pixels."""
    try:
        source = SD(str(path), SDC.READ)
        try:
            datasets = source.datasets()
            required = (SOURCE_VARIABLE, "CMG 0.05 Deg Monthly EVI", SOURCE_QUALITY)
            if any(name not in datasets for name in required):
                return False
            if not all(tuple(datasets[name][1]) == (3600, 7200) for name in required):
                return False
            return not read_pixels or all(
                tuple(source.select(name).get().shape) == (3600, 7200) for name in required
            )
        finally:
            source.end()
    except (HDF4Error, OSError):
        return False


def _download_one_granule(granule: object, staging_dir: Path, raw_dir: Path) -> Path:
    """Download a granule with HTTP byte-range resume and HDF verification."""
    native_id = str(granule["meta"]["native-id"])  # type: ignore[index]
    urls = granule.data_links(access="https")  # type: ignore[attr-defined]
    if not urls:
        raise RuntimeError(f"CMR supplied no HTTPS data link for {native_id}")
    url = urls[0]
    filename = urlparse(url).path.rsplit("/", 1)[-1]
    destination = raw_dir / filename
    if _valid_granule(destination):
        return destination
    partial = staging_dir / f"{filename}.part"
    if partial.exists() and _valid_granule(partial):
        partial.replace(destination)
        return destination
    store = earthaccess.__store__
    original_session = store.get_requests_session()
    store._clone_session_in_local_thread(original_session)
    session = store.thread_locals.local_thread_session

    for attempt in range(DOWNLOAD_ATTEMPTS):
        offset = partial.stat().st_size if partial.exists() else 0
        try:
            with session.get(
                url,
                headers={"Range": f"bytes={offset}-"},
                stream=True,
                allow_redirects=True,
                timeout=(30, 180),
            ) as response:
                response.raise_for_status()
                content_range = response.headers.get("Content-Range", "")
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
                if offset and response.status_code == 206 and (
                    not match or int(match.group(1)) != offset
                ):
                    raise OSError("Server returned a mismatched byte range")
                if response.status_code == 200 and offset:
                    offset = 0
                total = int(match.group(3)) if match else None
                if total is None and response.headers.get("Content-Length"):
                    total = offset + int(response.headers["Content-Length"])
                mode = "ab" if offset and response.status_code == 206 else "wb"
                with partial.open(mode) as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
            if total is not None and partial.stat().st_size != total:
                raise OSError(
                    f"Incomplete transfer for {native_id}: "
                    f"{partial.stat().st_size} of {total} bytes"
                )
            if not _valid_granule(partial):
                raise OSError(f"Downloaded HDF4 granule failed validation: {native_id}")
            partial.replace(destination)
            return destination
        except (requests.RequestException, OSError) as error:
            if attempt + 1 == DOWNLOAD_ATTEMPTS:
                raise RuntimeError(
                    f"Could not download a complete verified MOD13C2 granule: {native_id}"
                ) from error
            time.sleep(min(2**attempt, 60))
    raise AssertionError("Download retry loop exhausted unexpectedly")


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
    """Normalize the longest complete cached monthly run into chunked Zarr."""
    if variable not in {"ndvi", "evi"}:
        raise ValueError("MODIS vegetation variable must be 'ndvi' or 'evi'")
    output = output or Path(f"data/processed/modis_{variable}.zarr")
    entries = sorted(
        (
            pd.Period(datetime.strptime(path.name.split(".")[1][1:], "%Y%j"), freq="M"),
            path,
        )
        for path in raw_dir.glob("MOD13C2.A*.061.*.hdf")
    )
    if len({period for period, _ in entries}) != len(entries):
        raise ValueError("Multiple MOD13C2 granules were found for one calendar month")
    runs: list[list[tuple[pd.Period, Path]]] = []
    for entry in entries:
        if not runs or entry[0].ordinal != runs[-1][-1][0].ordinal + 1:
            runs.append([entry])
        else:
            runs[-1].append(entry)
    files = max(runs, key=len, default=[])
    if len(files) < 120:
        raise ValueError(
            "At least 120 monthly MOD13C2 granules are required for trend analysis; "
            f"the longest uninterrupted local run has {len(files)}."
        )
    values: list[np.ndarray] = []
    dates: list[pd.Timestamp] = []
    for _, path in files:
        acquisition = path.name.split(".")[1]
        dates.append(pd.Timestamp(datetime.strptime(acquisition[1:], "%Y%j")))
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
                "Longest uninterrupted run of verified granules selected; scale factor "
                "1/10000; fill, invalid values, and quality ranks >1 masked; monthly values "
                "averaged spatially."
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
    load_dotenv()
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
    staging_dir = raw_dir / ".staging"
    staging_dir.mkdir(exist_ok=True)
    for staged_path in staging_dir.glob("*.hdf"):
        destination = raw_dir / staged_path.name
        if not _valid_granule(staged_path, read_pixels=True):
            staged_path.unlink()
        elif _valid_granule(destination):
            staged_path.unlink()
        else:
            staged_path.replace(destination)
    for partial in staging_dir.glob("*.hdf.part"):
        destination = raw_dir / partial.name.removesuffix(".part")
        if _valid_granule(partial, read_pixels=True):
            if _valid_granule(destination):
                partial.unlink()
            else:
                partial.replace(destination)
    existing: set[str] = set()
    for path in raw_dir.glob("MOD13C2.A*.061.*.hdf"):
        if _valid_granule(path):
            existing.add(path.stem)
        else:
            path.unlink()
    missing = [item for item in granules if item["meta"]["native-id"] not in existing]
    if not missing:
        return []
    completed: list[Path] = []
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        futures = {
            executor.submit(_download_one_granule, granule, staging_dir, raw_dir): granule
            for granule in missing
        }
        for future in as_completed(futures):
            completed.append(future.result())
    return completed
