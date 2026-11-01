"""Export gridded trend statistics as a multiband Cloud Optimized GeoTIFF."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from rasterio.shutil import copy as raster_copy
from rasterio.transform import from_bounds

_BANDS = (
    "slope_ols",
    "slope_ols_lo",
    "slope_ols_hi",
    "p_ols",
    "slope",
    "slope_lo",
    "slope_hi",
    "p_mk",
    "p_value",
    "n_valid",
    "significant_fdr",
    "sign_class",
)


def write_trend_cog(dataset: xr.Dataset, destination: Path) -> Path:
    """Write all trend statistics to a north-up EPSG:4326 COG."""
    missing = set(_BANDS) - set(dataset.data_vars)
    if missing:
        raise ValueError(f"Trend dataset is missing COG bands: {', '.join(sorted(missing))}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    intermediate = destination.with_suffix(".intermediate.tif")
    height = dataset.sizes["lat"]
    width = dataset.sizes["lon"]
    array = np.stack(
        [np.asarray(dataset[name].transpose("lat", "lon").values)[::-1] for name in _BANDS]
    ).astype(np.float32)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": len(_BANDS),
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": from_bounds(-180, -90, 180, 90, width, height),
        "nodata": np.nan,
        "compress": "DEFLATE",
    }
    try:
        with rasterio.open(intermediate, "w", **profile) as target:
            target.write(array)
            for index, name in enumerate(_BANDS, start=1):
                target.set_band_description(index, name)
        raster_copy(
            intermediate,
            destination,
            driver="COG",
            compress="DEFLATE",
            blocksize=256,
            overview_resampling="NEAREST",
        )
    finally:
        intermediate.unlink(missing_ok=True)
    return destination
