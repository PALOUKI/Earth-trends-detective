"""Area-weighted extraction of rectangular regions from the processed grid."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from pipeline.trends.base import analyze_series, deseasonalize_monthly

DATASET_PATH = Path("data/processed/gistemp_tas_anom.zarr")


def area_weighted_region_series(
    dataset: xr.Dataset,
    bounds: tuple[float, float, float, float],
    variable_name: str = "temperature_anomaly",
) -> xr.DataArray:
    """Return cosine-latitude-weighted mean for (west, south, east, north)."""
    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError(
            "Bounds must satisfy -180 <= west < east <= 180 and -90 <= south < north <= 90"
        )
    if variable_name not in dataset:
        raise ValueError(f"Processed dataset does not contain variable {variable_name!r}")
    subset = dataset[variable_name].sel(lat=slice(south, north), lon=slice(west, east))
    if subset.sizes.get("lat", 0) == 0 or subset.sizes.get("lon", 0) == 0:
        raise ValueError("Region does not intersect any grid cell")
    weights = np.cos(np.deg2rad(subset.lat)).clip(min=0)
    return subset.weighted(weights).mean(("lat", "lon"), skipna=True).rename(variable_name)


def analyze_region(
    bounds: tuple[float, float, float, float],
    start: str | None = None,
    end: str | None = None,
    dataset_path: Path = DATASET_PATH,
    variable_name: str = "temperature_anomaly",
) -> dict[str, object]:
    """Extract a regional GISTEMP series, deseasonalize it, and calculate trends."""
    with xr.open_zarr(dataset_path) as dataset:
        series = area_weighted_region_series(dataset, bounds, variable_name)
        if start:
            series = series.sel(time=slice(start, None))
        if end:
            series = series.sel(time=slice(None, end))
        raw = np.asarray(series.compute(scheduler="synchronous").values, dtype=np.float64)
        adjusted, seasonal = deseasonalize_monthly(raw)
        result = analyze_series(adjusted)
        dates = series.time.values.astype("datetime64[M]").astype(str).tolist()
    return {
        "bounds": {"west": bounds[0], "south": bounds[1], "east": bounds[2], "north": bounds[3]},
        "time": dates,
        "value": raw.tolist(),
        "seasonal": seasonal.tolist(),
        "anomaly": adjusted.tolist(),
        "trend": result,
    }
