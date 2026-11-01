import asyncio
import json
from pathlib import Path

import numpy as np
import xarray as xr
from httpx import ASGITransport, AsyncClient

from api.app.main import app


def test_precomputed_xyz_tiles_are_described_and_served(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    tile_root = Path("data/tiles/gistemp_tas_anom/full")
    tile_root.mkdir(parents=True)
    tile = tile_root / "slope/0/0/0.png"
    tile.parent.mkdir(parents=True)
    tile.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    (tile_root / "palette.json").write_text(
        json.dumps(
            {
                "bounds": [[-180, 90], [180, 90], [180, -90], [-180, -90]],
                "slope_unit": "K/year",
                "scale_min": -0.1,
                "scale_max": 0.1,
                "scale_percentile": 98,
                "minzoom": 0,
                "maxzoom": 5,
                "tile_size": 256,
                "tile_scheme": "XYZ / WebMercatorQuad",
                "palette": {"negative": "#2166ac", "zero": "#f7f7f7", "positive": "#b2182b"},
                "layers": {},
                "interpretation": "Test map.",
            }
        )
    )
    trend_store = Path("data/processed/gistemp_tas_anom/trend_full.zarr")
    trend_store.parent.mkdir(parents=True)
    xr.Dataset(
        {
            "slope_ols": (("lat", "lon"), [[0.1, -0.1], [0.0, np.nan]]),
            "sign_class": (("lat", "lon"), [[1, -1], [0, 0]]),
        },
        coords={"lat": [0.0, 2.0], "lon": [0.0, 2.0]},
    ).to_zarr(trend_store, zarr_format=2)

    async def run_requests():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            metadata = await client.get("/api/trend/gistemp_tas_anom?window=full")
            response = await client.get("/tiles/gistemp_tas_anom/full/slope/0/0/0.png")
            invalid = await client.get("/tiles/gistemp_tas_anom/full/slope/6/0/0.png")
            return metadata, response, invalid

    metadata, response, invalid = asyncio.run(run_requests())

    assert metadata.status_code == 200
    assert metadata.json()["slope_unit"] == "K/year"
    assert metadata.json()["minzoom"] == 0
    assert metadata.json()["maxzoom"] == 5
    assert metadata.json()["statistics"] == {
        "valid_cells": 3,
        "significant_increase_cells": 1,
        "significant_decrease_cells": 1,
        "non_significant_cells": 1,
    }
    assert metadata.json()["urls"]["slope"].endswith("/slope/{z}/{x}/{y}.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")
    assert response.headers["cache-control"] == "public, max-age=31536000"
    assert invalid.status_code == 404
