import asyncio

import numpy as np
import pandas as pd
import xarray as xr
from httpx import ASGITransport, AsyncClient

from api.app import main
from api.app.schemas import RegionDefinition


def test_region_endpoint_returns_trend_summary_from_data(tmp_path, monkeypatch) -> None:
    time = pd.date_range("2000-01-01", periods=120, freq="MS")
    years = np.arange(120) / 12
    values = (0.03 * years)[:, None, None] * np.ones((120, 2, 2))
    data = xr.Dataset(
        {"temperature_anomaly": (("time", "lat", "lon"), values)},
        coords={"time": time, "lat": [-1.0, 1.0], "lon": [-1.0, 1.0]},
    )
    path = tmp_path / "gistemp.zarr"
    data.to_zarr(path, zarr_format=2)
    monkeypatch.setattr(main, "DATASET_PATH", path)
    monkeypatch.setattr(
        main,
        "REGIONS",
        [
            RegionDefinition(
                id=region_id,
                name=region_id,
                name_fr=region_id,
                bounds=(-1, -1, 1, 1),
                description="test",
                description_fr="test",
            )
            for region_id in ("amazon", "sahara")
        ],
    )

    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            regional = await client.post(
                "/api/region",
                json={
                    "variable": "gistemp_tas_anom",
                    "bounds": [-2, -2, 2, 2],
                    "start": "2000-01",
                    "end": "2009-12",
                    "label": "Test region",
                },
            )
            point = await client.get("/api/point?lat=-0.9&lon=-0.9")
            comparison = await client.get(
                "/api/compare?variable=gistemp_tas_anom&a=amazon&b=sahara"
            )
            docs = await client.get("/docs")
            suggestions = await client.get("/api/suggest?theme=climate&place=Amazon")
            return regional, point, comparison, docs, suggestions

    response, point, comparison, docs, suggestions = asyncio.run(send_request())
    payload = response.json()

    assert response.status_code == 200
    assert payload["trend"]["n_valid"] == 120
    assert payload["trend"]["slope_ols"] > 0
    assert set(payload["summary"]) == {"en", "fr"}
    assert payload["variable"] == "gistemp_tas_anom"
    assert "break" in payload
    assert payload["break"]["date"] in payload["time"]
    assert point.status_code == 200
    assert point.json()["location"] == {"lat": -1.0, "lon": -1.0}
    assert point.json()["period"] == {"start": "2000-01", "end": "2009-12"}
    assert comparison.status_code == 200
    assert set(comparison.json()) == {"a", "b"}
    assert docs.status_code == 200
    assert suggestions.status_code == 200
    assert suggestions.json()[0]["region_id"] == "amazon"


def test_unprocessed_verified_variable_is_reported_as_temporarily_unavailable(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setitem(main.VARIABLE_CONFIG["modis_ndvi"], "path", tmp_path / "missing.zarr")
    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            return await client.post(
                "/api/region",
                json={
                    "variable": "modis_ndvi",
                    "bounds": [-10, -10, 10, 10],
                    "label": "MODIS sample",
                },
            )

    response = asyncio.run(send_request())
    assert response.status_code == 503


def test_modis_variable_uses_its_own_field_source_and_units(tmp_path, monkeypatch) -> None:
    time = pd.date_range("2000-01-01", periods=120, freq="MS")
    values = (0.002 * np.arange(120) / 12)[:, None, None] * np.ones((120, 2, 2))
    dataset = xr.Dataset(
        {"ndvi_index": (("time", "lat", "lon"), values)},
        coords={"time": time, "lat": [-1.0, 1.0], "lon": [-1.0, 1.0]},
    )
    path = tmp_path / "modis_ndvi.zarr"
    dataset.to_zarr(path, zarr_format=2)
    monkeypatch.setitem(main.VARIABLE_CONFIG["modis_ndvi"], "path", path)

    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            return await client.post(
                "/api/region",
                json={
                    "variable": "modis_ndvi",
                    "bounds": [-2, -2, 2, 2],
                    "label": "Synthetic test area",
                },
            )

    response = asyncio.run(send_request())
    assert response.status_code == 200
    assert response.json()["variable"] == "modis_ndvi"
    assert response.json()["unit"] == "1"
    assert "MODIS normalized difference vegetation index (NDVI)" in response.json()["summary"]["en"]
