"""Download and normalize NASA GISS GISTEMP v4 gridded anomalies."""

from __future__ import annotations

import gzip
import shutil
import urllib.request
from pathlib import Path

import pandas as pd
import xarray as xr

SOURCE_URL = "https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz"
RAW_GZIP = Path("data/raw/gistemp1200_GHCNv4_ERSSTv5.nc.gz")
RAW_NETCDF = Path("data/raw/gistemp1200_GHCNv4_ERSSTv5.nc")
OUTPUT = Path("data/processed/gistemp_tas_anom.zarr")


def download_gistemp(destination: Path = RAW_GZIP) -> Path:
    """Download the NASA GISS public gzip file if it is not already cached."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        request = urllib.request.Request(
            SOURCE_URL, headers={"User-Agent": "earth-trends-detective/0.1"}
        )
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            destination.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
    return destination


def prepare_gistemp(
    source: Path = RAW_GZIP,
    netcdf_path: Path = RAW_NETCDF,
    output: Path = OUTPUT,
) -> Path:
    """Normalize GISTEMP coordinates, mask sparse cells, and write chunked Zarr."""
    netcdf_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "rb") as compressed, netcdf_path.open("wb") as raw:
        shutil.copyfileobj(compressed, raw)

    with xr.open_dataset(netcdf_path, engine="netcdf4") as source_ds:
        if "tempanomaly" not in source_ds:
            raise ValueError("NASA GISTEMP file does not contain the expected tempanomaly variable")
        values = source_ds["tempanomaly"].rename("temperature_anomaly")
        ds = values.to_dataset()
        # NASA's native cells are centered at odd degrees and already run west-to-east.
        lon = ((ds.lon + 180) % 360) - 180
        ds = ds.assign_coords(lon=lon).sortby("lon").sortby("lat")
        monthly_time = pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp()
        ds = ds.assign_coords(time=monthly_time)
        n_valid = ds.temperature_anomaly.notnull().sum("time").astype("int16")
        valid = (n_valid >= int(ds.sizes["time"] * 0.70)) & (n_valid >= 120)
        ds["temperature_anomaly"] = ds.temperature_anomaly.where(valid)
        ds["n_valid"] = n_valid
        ds.temperature_anomaly.attrs = {
            "long_name": "Monthly surface temperature anomaly",
            "units": "K",
            "source_variable": "tempanomaly",
            "seasonal_adjustment": "Already provided as monthly anomalies by NASA GISTEMP v4",
        }
        ds["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
        ds.attrs = {
            "title": "NASA GISS GISTEMP v4 Land-Ocean Temperature Index anomalies",
            "source": "NASA Goddard Institute for Space Studies",
            "source_url": SOURCE_URL,
            "version": "GISTEMP v4; file history created 2026-10-08",
            "doi": "10.1029/2023JD040179",
            "crs": "EPSG:4326",
            "grid": "regular 2 degree by 2 degree; native GISTEMP grid",
            "processing": (
                "Coordinates normalized; monthly time set to first of month; cells require "
                ">=70% coverage and >=120 valid months."
            ),
        }
        ds = ds.chunk({"time": -1, "lat": 30, "lon": 30})
        output.parent.mkdir(parents=True, exist_ok=True)
        ds.to_zarr(output, mode="w", zarr_format=2)
    return output


def ingest() -> Path:
    """Run cached source download followed by Zarr preprocessing."""
    download_gistemp()
    return prepare_gistemp()
