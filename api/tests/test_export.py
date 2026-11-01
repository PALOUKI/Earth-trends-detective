import asyncio
import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from httpx import ASGITransport, AsyncClient

from api.app import main


def test_api_exports_regional_csv_and_map_png(tmp_path, monkeypatch) -> None:
    time = pd.date_range("2000-01-01", periods=36, freq="MS")
    years = np.arange(time.size) / 12
    values = (0.02 * years)[:, None, None] * np.ones((time.size, 2, 2))
    dataset = xr.Dataset(
        {"temperature_anomaly": (("time", "lat", "lon"), values)},
        coords={"time": time, "lat": [-1.0, 1.0], "lon": [-1.0, 1.0]},
    )
    source = tmp_path / "gistemp.zarr"
    dataset.to_zarr(source, zarr_format=2)
    monkeypatch.setattr(main, "DATASET_PATH", source)
    monkeypatch.chdir(tmp_path)
    map_path = Path("data/tiles/gistemp_tas_anom/full/slope.png")
    map_path.parent.mkdir(parents=True)
    map_path.write_bytes(b"\x89PNG\r\n\x1a\nfixture")

    async def requests():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            series = await client.get(
                "/api/export?format=csv&west=-2&south=-2&east=2&north=2"
            )
            image = await client.get("/api/export?format=png&window=full&layer=slope")
            return series, image

    series, image = asyncio.run(requests())
    rows = list(csv.reader(io.StringIO(series.text)))

    assert series.status_code == 200
    assert series.headers["content-type"].startswith("text/csv")
    assert rows[0] == ["month", "value_K", "seasonal_cycle_K", "deseasonalized_anomaly_K"]
    assert len(rows) == 37
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")
