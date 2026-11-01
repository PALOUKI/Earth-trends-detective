"""Generate transparent XYZ trend and nonsignificance tiles with rio-tiler."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import xarray as xr
from rasterio.enums import ColorInterp
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.io import Reader

from pipeline.tiling.png import encode_rgba_png

NEGATIVE = (33, 102, 172)
NEUTRAL = (247, 247, 247)
POSITIVE = (178, 24, 43)
WORLD_BOUNDS = (-180.0, -90.0, 180.0, 90.0)


def _diverging_color(value: float, limit: float) -> tuple[int, int, int, int]:
    position = float(np.clip((value / limit + 1) / 2, 0, 1))
    left, right, amount = (
        (NEGATIVE, NEUTRAL, position * 2)
        if position < 0.5
        else (NEUTRAL, POSITIVE, (position - 0.5) * 2)
    )
    rgb = tuple(round(a + amount * (b - a)) for a, b in zip(left, right, strict=True))
    return (*rgb, 255)


def _write_xyz_tiles(
    rgba: np.ndarray,
    output_dir: Path,
    *,
    max_zoom: int,
    resampling_method: str = "nearest",
) -> None:
    """Reproject an RGBA array into Web Mercator XYZ PNGs.

    Nearest-neighbor keeps the native 2-degree grid visible and avoids spreading
    positive slope colors into a blurred wash. Transparent missing cells stay masked.
    """
    height, width, _ = rgba.shape
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 4,
        "dtype": "uint8",
        "crs": "EPSG:4326",
        "transform": from_bounds(*WORLD_BOUNDS, width, height),
        "photometric": "RGB",
        "compress": "deflate",
    }
    with MemoryFile() as memory_file:
        with memory_file.open(**profile) as source:
            source.write(np.moveaxis(rgba, -1, 0))
            source.colorinterp = (
                ColorInterp.red,
                ColorInterp.green,
                ColorInterp.blue,
                ColorInterp.alpha,
            )
        with memory_file.open() as source:
            with Reader(None, dataset=source) as reader:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="Adjusting dataset latitudes to avoid re-projection overflow",
                        category=UserWarning,
                    )
                    for zoom in range(max_zoom + 1):
                        side = 1 << zoom
                        for x in range(side):
                            for y in range(side):
                                try:
                                    tile = reader.tile(
                                        x,
                                        y,
                                        zoom,
                                        tilesize=256,
                                        resampling_method=resampling_method,
                                    )
                                except TileOutsideBounds:
                                    continue
                                destination = output_dir / str(zoom) / str(x) / f"{y}.png"
                                destination.parent.mkdir(parents=True, exist_ok=True)
                                destination.write_bytes(
                                    tile.render(img_format="PNG", add_mask=False)
                                )


def _slope_rgba(slope: np.ndarray, limit: float) -> np.ndarray:
    """Apply a symmetric blue-neutral-red palette and transparent missing cells."""
    image = np.zeros((*slope.shape, 4), dtype=np.uint8)
    for row, col in np.argwhere(np.isfinite(slope)):
        image[row, col] = _diverging_color(float(slope[row, col]), limit)
    return image


def _stipple_rgba(slope: np.ndarray, significant: np.ndarray) -> np.ndarray:
    """Place one small black stipple at each valid cell that fails map FDR."""
    height, width = slope.shape
    image = np.zeros((height * 2, width * 2, 4), dtype=np.uint8)
    valid_nonsignificant = np.isfinite(slope) & ~significant
    for row, col in np.argwhere(valid_nonsignificant):
        image[row * 2 + 1, col * 2 + 1] = (20, 20, 20, 210)
    return image


def render_trend_map(
    trends_path: Path,
    output_dir: Path,
    scale_percentile: float = 98,
    max_zoom: int = 5,
) -> dict[str, object]:
    """Write slope and nonsignificance XYZ tiles for zooms zero through five."""
    if not 0 <= max_zoom <= 5:
        raise ValueError("The MVP tile zoom range must be between 0 and 5")
    with xr.open_zarr(trends_path) as dataset:
        slope = np.asarray(dataset.slope_ols.transpose("lat", "lon").values, dtype=float)[::-1]
        significant = np.asarray(
            dataset.significant_fdr.transpose("lat", "lon").values, dtype=bool
        )[::-1]

    finite = np.abs(slope[np.isfinite(slope)])
    if finite.size == 0:
        raise ValueError("Trend grid has no finite slope values")
    limit = float(np.percentile(finite, scale_percentile))
    if limit == 0:
        limit = 1e-12

    output_dir.mkdir(parents=True, exist_ok=True)
    slope_image = _slope_rgba(slope, limit)
    stipple_image = _stipple_rgba(slope, significant)
    _write_xyz_tiles(
        slope_image,
        output_dir / "slope",
        max_zoom=max_zoom,
        resampling_method="nearest",
    )
    _write_xyz_tiles(
        stipple_image,
        output_dir / "nonsignificant",
        max_zoom=max_zoom,
        resampling_method="nearest",
    )
    height, width = slope.shape
    (output_dir / "slope.png").write_bytes(
        encode_rgba_png(slope_image.tobytes(), width, height)
    )
    (output_dir / "nonsignificant.png").write_bytes(
        encode_rgba_png(stipple_image.tobytes(), width * 2, height * 2)
    )
    metadata: dict[str, object] = {
        "bounds": [[-180, 90], [180, 90], [180, -90], [-180, -90]],
        "slope_unit": "K/year",
        "slope_method": "OLS linear trend",
        "significance_method": "Hamed-Rao modified Mann-Kendall with Benjamini-Hochberg FDR",
        "scale_min": -limit,
        "scale_max": limit,
        "scale_percentile": scale_percentile,
        "minzoom": 0,
        "maxzoom": max_zoom,
        "tile_size": 256,
        "tile_scheme": "XYZ / WebMercatorQuad",
        "palette": {
            "negative": "#2166ac",
            "zero": "#f7f7f7",
            "positive": "#b2182b",
        },
        "layers": {
            "slope": "slope/{z}/{x}/{y}.png",
            "nonsignificant": "nonsignificant/{z}/{x}/{y}.png",
        },
        "interpretation": (
            "Transparent pixels indicate missing values; black stipple dots mark cells "
            "not significant after Benjamini-Hochberg FDR."
        ),
    }
    (output_dir / "palette.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata
