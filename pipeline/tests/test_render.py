import json

import numpy as np
import xarray as xr

from pipeline.tiling.render import _slope_rgba, render_trend_map


def test_slope_render_keeps_missing_cells_transparent() -> None:
    image = _slope_rgba(np.array([[0.1, np.nan]]), limit=0.2)

    assert image[0, 0, 3] == 255
    assert image[0, 1, 3] == 0


def test_render_builds_xyz_slope_and_stipple_tiles(tmp_path) -> None:
    source = tmp_path / "trends.zarr"
    slope = np.linspace(-0.2, 0.2, 32, dtype=float).reshape(4, 8)
    slope[0, 0] = np.nan
    significant = np.zeros((4, 8), dtype=bool)
    significant[1, 2] = True
    dataset = xr.Dataset(
        {
            "slope_ols": (("lat", "lon"), slope),
            "significant_fdr": (("lat", "lon"), significant),
        },
        coords={"lat": [-67.5, -22.5, 22.5, 67.5], "lon": np.linspace(-157.5, 157.5, 8)},
    )
    dataset.to_zarr(source, zarr_format=2)

    metadata = render_trend_map(
        source, tmp_path / "output", max_zoom=1, slope_unit="index/year"
    )

    assert (tmp_path / "output/slope.png").read_bytes().startswith(b"\x89PNG")
    assert (tmp_path / "output/nonsignificant.png").read_bytes().startswith(b"\x89PNG")
    for zoom in range(2):
        side = 1 << zoom
        assert (tmp_path / f"output/slope/{zoom}/0/0.png").is_file()
        assert (tmp_path / f"output/slope/{zoom}/{side - 1}/{side - 1}.png").is_file()
        assert (tmp_path / f"output/nonsignificant/{zoom}/0/0.png").is_file()
        assert (tmp_path / f"output/nonsignificant/{zoom}/{side - 1}/{side - 1}.png").is_file()
    assert metadata["scale_min"] == -metadata["scale_max"]
    assert metadata["minzoom"] == 0
    assert metadata["maxzoom"] == 1
    saved = json.loads((tmp_path / "output/palette.json").read_text())
    assert saved["slope_unit"] == "index/year"
    assert saved["slope_method"] == "OLS linear trend"
    assert saved["tile_scheme"] == "XYZ / WebMercatorQuad"


def test_mvp_tile_generator_rejects_zoom_levels_above_five(tmp_path) -> None:
    source = tmp_path / "trends.zarr"
    dataset = xr.Dataset(
        {
            "slope_ols": (("lat", "lon"), [[0.1]]),
            "significant_fdr": (("lat", "lon"), [[True]]),
        },
        coords={"lat": [0.0], "lon": [0.0]},
    )
    dataset.to_zarr(source, zarr_format=2)

    try:
        render_trend_map(source, tmp_path / "output", max_zoom=6)
    except ValueError as error:
        assert "between 0 and 5" in str(error)
    else:
        raise AssertionError("Zoom 6 must be rejected by the MVP tile generator")
