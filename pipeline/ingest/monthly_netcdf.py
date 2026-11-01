"""Ingest selected monthly MERRA-2 and GLDAS NetCDF fields from GES DISC."""

from __future__ import annotations

import re
from pathlib import Path

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv

PRODUCTS = {
    "merra2_flux": {
        "short_name": "M2TMNXFLX",
        "version": "5.12.4",
        "field": "EVAP",
        "unit": "kg m-2 s-1",
        "raw_dir": Path("data/raw/merra2_flux"),
        "output": Path("data/processed/merra2_flux.zarr"),
        "filename_pattern": r"MERRA2_\d+\.tavgM_2d_flx_Nx\.(\d{4})(\d{2})\.nc4$",
        "name": "MERRA-2 monthly evaporation flux",
        "name_fr": "Flux d'évaporation mensuel MERRA-2",
        "source": "NASA GMAO MERRA-2 M2TMNXFLX v5.12.4",
        "doi": "10.5067/0JRLVL8YV2Y4",
        "title": "NASA MERRA-2 monthly turbulent evaporation flux",
    },
    "gldas_noah_monthly": {
        "short_name": "GLDAS_NOAH025_M",
        "version": "2.1",
        "field": "SoilMoi0_10cm_inst",
        "unit": "kg m-2",
        "raw_dir": Path("data/raw/gldas_noah_monthly"),
        "output": Path("data/processed/gldas_noah_monthly.zarr"),
        "filename_pattern": r"GLDAS_NOAH025_M\.A(\d{4})(\d{2})\.021\.nc4$",
        "name": "GLDAS Noah monthly 0–10 cm soil moisture",
        "name_fr": "Humidité du sol GLDAS Noah à 0–10 cm",
        "source": "NASA GLDAS Noah 0.25° monthly v2.1",
        "doi": "10.5067/SXAVCZFAQLNO",
        "title": "NASA GLDAS Noah monthly near-surface soil moisture",
    },
}

TARGET_LAT = np.arange(-89.0, 90.0, 2.0)
TARGET_LON = np.arange(-179.0, 180.0, 2.0)


def _config(variable: str) -> dict[str, object]:
    try:
        return PRODUCTS[variable]
    except KeyError as error:
        raise ValueError(f"No monthly NetCDF ingester is configured for {variable}") from error


def _valid_file(path: Path, config: dict[str, object]) -> bool:
    """Read the selected full monthly data field and verify its actual units/date."""
    if not re.search(str(config["filename_pattern"]), path.name):
        return False
    try:
        with xr.open_dataset(path) as dataset:
            field = str(config["field"])
            if field not in dataset or not {"time", "lat", "lon"}.issubset(
                dataset[field].dims
            ):
                return False
            if dataset[field].attrs.get("units") != config["unit"]:
                return False
            if dataset.sizes.get("time") != 1:
                return False
            values = dataset[field].isel(time=0).load().values
            return values.shape == (dataset.sizes["lat"], dataset.sizes["lon"])
    except (OSError, ValueError, KeyError):
        return False


def download_monthly_netcdf(
    variable: str,
    *,
    start: str = "2000-01-01",
    end: str = "2009-12-31",
) -> list[Path]:
    """Search and download ten years of real, file-verified monthly granules."""
    config = _config(variable)
    load_dotenv()
    if not earthaccess.login(strategy="environment", persist=False):
        raise RuntimeError("Earthdata Login failed; check the local environment credentials.")
    granules = earthaccess.search_data(
        short_name=str(config["short_name"]),
        version=str(config["version"]),
        temporal=(start, end),
        count=250,
    )
    if not granules:
        raise RuntimeError(
            f"CMR returned no {config['short_name']} v{config['version']} granules "
            f"for {start}–{end}"
        )
    raw_dir = Path(config["raw_dir"])
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
        if not _valid_file(destination, config):
            if destination.exists():
                destination.replace(destination.with_suffix(destination.suffix + ".partial"))
            pending.append(granule)
    files = earthaccess.download(pending, str(raw_dir)) if pending else []
    downloaded = [Path(path) for path in files]
    bad_files = [path for path in downloaded if not _valid_file(path, config)]
    if bad_files:
        names = ", ".join(path.name for path in bad_files[:5])
        raise RuntimeError(f"Download produced invalid monthly NetCDF files: {names}")
    return downloaded


def _read_month(path: Path, config: dict[str, object]) -> tuple[pd.Timestamp, np.ndarray]:
    """Read one monthly field, normalize coordinates, and interpolate to the 2° grid."""
    filename_date = re.search(str(config["filename_pattern"]), path.name)
    if not filename_date:
        raise ValueError(f"Unexpected source filename: {path.name}")
    time = pd.Timestamp(year=int(filename_date.group(1)), month=int(filename_date.group(2)), day=1)
    with xr.open_dataset(path) as dataset:
        field = str(config["field"])
        if field not in dataset or dataset[field].attrs.get("units") != config["unit"]:
            raise ValueError(
                f"Selected field or unit differs from verified metadata in {path.name}"
            )
        values = dataset[field].isel(time=0).assign_coords(
            lon=((dataset.lon + 180) % 360) - 180
        )
        for key in ("_FillValue", "missing_value", "fmissing_value"):
            missing = values.attrs.get(key)
            if missing is not None:
                values = values.where(values != float(np.asarray(missing).reshape(-1)[0]))
        values = values.sortby("lat").sortby("lon")
        gridded = values.interp(lat=TARGET_LAT, lon=TARGET_LON, method="linear")
        array = np.asarray(gridded.values, dtype=np.float32)
    return time, array


def prepare_monthly_netcdf(
    variable: str,
    *,
    raw_dir: Path | None = None,
    output: Path | None = None,
) -> Path:
    """Write a 2° monthly Zarr with missing months preserved and coverage masked."""
    config = _config(variable)
    raw_dir = raw_dir or Path(config["raw_dir"])
    output = output or Path(config["output"])
    paths = sorted(path for path in raw_dir.glob("*.nc4") if _valid_file(path, config))
    if not paths:
        raise FileNotFoundError(f"No validated monthly files for {variable} under {raw_dir}")
    records = sorted((_read_month(path, config) for path in paths), key=lambda record: record[0])
    observed = pd.DatetimeIndex([record[0] for record in records])
    if observed.has_duplicates:
        raise ValueError(f"Duplicate monthly files found for {variable}")
    times = pd.date_range(observed[0], observed[-1], freq="MS")
    monthly = np.full((times.size, TARGET_LAT.size, TARGET_LON.size), np.nan, dtype=np.float32)
    for month, values in records:
        monthly[times.get_loc(month)] = values
    n_valid = np.isfinite(monthly).sum(axis=0).astype(np.int16)
    enough_data = (n_valid >= 120) & (n_valid >= int(times.size * 0.70))
    monthly[:, ~enough_data] = np.nan
    dataset = xr.Dataset(
        {
            str(config["field"]).lower(): (("time", "lat", "lon"), monthly),
            "n_valid": (("lat", "lon"), n_valid),
        },
        coords={"time": times, "lat": TARGET_LAT, "lon": TARGET_LON},
        attrs={
            "title": str(config["title"]),
            "source": str(config["source"]),
            "short_name": str(config["short_name"]),
            "version": str(config["version"]),
            "doi": str(config["doi"]),
            "source_field": str(config["field"]),
            "crs": "EPSG:4326",
            "grid": "source grid linearly interpolated to regular 2 degree cell centers",
            "processing": (
                "Source fill values are masked by xarray; each monthly source field is "
                "bilinearly interpolated to the 2-degree analysis grid. Missing months are "
                "retained as NaN; cells require 120 valid months and 70 percent coverage."
            ),
        },
    )
    output_field = str(config["field"]).lower()
    dataset[output_field].attrs = {
        "long_name": str(config["name"]),
        "units": str(config["unit"]),
        "source_variable": str(config["field"]),
    }
    dataset["n_valid"].attrs = {"long_name": "Number of valid monthly observations", "units": "1"}
    dataset = dataset.chunk({"time": -1, "lat": 30, "lon": 30})
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_zarr(output, mode="w", zarr_format=2)
    return output
