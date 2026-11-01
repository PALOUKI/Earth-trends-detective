import json

import numpy as np
import xarray as xr

from pipeline.tiling.render import render_trend_map


def test_render_builds_slope_and_stipple_overlays(tmp_path) -> None:
    source = tmp_path / "trends.zarr"
    dataset = xr.Dataset(
        {
            "slope": (("lat", "lon"), [[-0.2, 0.0], [0.1, np.nan]]),
            "significant_fdr": (("lat", "lon"), [[True, False], [False, False]]),
        },
        coords={"lat": [-45.0, 45.0], "lon": [-90.0, 90.0]},
    )
    dataset.to_zarr(source, zarr_format=2)

    metadata = render_trend_map(source, tmp_path / "output")

    assert (tmp_path / "output/slope.png").read_bytes().startswith(b"\x89PNG")
    assert (tmp_path / "output/nonsignificant.png").read_bytes().startswith(b"\x89PNG")
    assert metadata["scale_min"] == -metadata["scale_max"]
    saved = json.loads((tmp_path / "output/palette.json").read_text())
    assert saved["slope_unit"] == "K/year"
