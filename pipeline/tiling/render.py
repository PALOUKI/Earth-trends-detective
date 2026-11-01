"""Render 2° global slope and nonsignificance stipple overlays."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr

from pipeline.tiling.png import encode_rgba_png

NEGATIVE = (33, 102, 172)
NEUTRAL = (247, 247, 247)
POSITIVE = (178, 24, 43)


def _diverging_color(value: float, limit: float) -> tuple[int, int, int, int]:
    position = float(np.clip((value / limit + 1) / 2, 0, 1))
    left, right, amount = (
        (NEGATIVE, NEUTRAL, position * 2)
        if position < 0.5
        else (NEUTRAL, POSITIVE, (position - 0.5) * 2)
    )
    rgb = tuple(round(a + amount * (b - a)) for a, b in zip(left, right, strict=True))
    return (*rgb, 255)


def render_trend_map(
    trends_path: Path,
    output_dir: Path,
    scale_percentile: float = 98,
) -> dict[str, object]:
    """Write transparent PNG layers and palette metadata for MapLibre ImageSource."""
    with xr.open_zarr(trends_path) as ds:
        slope = np.asarray(ds.slope.transpose("lat", "lon").values, dtype=float)[::-1]
        significant = np.asarray(
            ds.significant_fdr.transpose("lat", "lon").values, dtype=bool
        )[::-1]
    finite = np.abs(slope[np.isfinite(slope)])
    if finite.size == 0:
        raise ValueError("Trend grid has no finite slope values")
    limit = float(np.percentile(finite, scale_percentile))
    if limit == 0:
        limit = 1e-12

    height, width = slope.shape
    rgba = bytearray(width * height * 4)
    stipple = bytearray(width * 2 * height * 2 * 4)
    for row in range(height):
        for col in range(width):
            value = slope[row, col]
            if np.isfinite(value):
                offset = (row * width + col) * 4
                rgba[offset : offset + 4] = bytes(_diverging_color(float(value), limit))
            if np.isfinite(value) and not significant[row, col]:
                # One dark point per 2x2 output block makes the non-significance
                # stipple visible when the 2° image is enlarged by the map.
                dot_row, dot_col = row * 2, col * 2
                offset = (dot_row * width * 2 + dot_col) * 4
                stipple[offset : offset + 4] = bytes((20, 20, 20, 190))

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "slope.png").write_bytes(encode_rgba_png(rgba, width, height))
    (output_dir / "nonsignificant.png").write_bytes(
        encode_rgba_png(stipple, width * 2, height * 2)
    )
    metadata: dict[str, object] = {
        "bounds": [[-180, 90], [180, 90], [180, -90], [-180, -90]],
        "slope_unit": "K/year",
        "scale_min": -limit,
        "scale_max": limit,
        "scale_percentile": scale_percentile,
        "palette": {
            "negative": "#2166ac",
            "zero": "#f7f7f7",
            "positive": "#b2182b",
        },
        "layers": {"slope": "slope.png", "nonsignificant": "nonsignificant.png"},
        "interpretation": (
            "Transparent pixels indicate missing values; black stipple dots mark cells "
            "not significant after Benjamini-Hochberg FDR."
        ),
    }
    (output_dir / "palette.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata
