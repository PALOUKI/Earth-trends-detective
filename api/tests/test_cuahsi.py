import asyncio
from calendar import monthrange

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import cuahsi
from api.app.main import app


def test_search_series_parses_metadata(monkeypatch):
    class Response:
        content = b"""<ArrayOfSeriesRecordFull><SeriesRecordFull>
        <SeriesCode>NWIS:site:00060</SeriesCode><Sitename>River gauge</Sitename>
        <location>NWIS:site</location><VarCode>NWIS:00060</VarCode>
        <VarName>Streamflow</VarName><VariableUnitsAbbrev>ft3/s</VariableUnitsAbbrev>
        <beginDate>2000-01-01</beginDate><endDate>2025-01-01</endDate>
        <latitude>40.0</latitude><longitude>-75.0</longitude><ServCode>NWIS</ServCode>
        <ServURL>https://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL</ServURL>
        <ValueCount>100</ValueCount></SeriesRecordFull></ArrayOfSeriesRecordFull>"""

        def raise_for_status(self):
            pass

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params):
            assert url == cuahsi.CATALOG_URL
            assert params["conceptKeyword"] == "discharge"
            return Response()

    monkeypatch.setattr(cuahsi.httpx, "AsyncClient", Client)
    import asyncio

    records = asyncio.run(
        cuahsi.search_series((-76, 39, -74, 41), "2000-01-01", "2025-01-01", "discharge")
    )
    assert records[0]["site"] == "River gauge"
    assert records[0]["unit"] == "ft3/s"
    assert records[0]["latitude"] == 40


def test_series_url_must_be_https_cuahsi_host(monkeypatch):
    monkeypatch.setattr(
        cuahsi.socket,
        "getaddrinfo",
        lambda *_: [(None, None, None, None, ("8.8.8.8", 0))],
    )
    assert (
        cuahsi._public_service_url("https://hydroportal.cuahsi.org/x.asmx?WSDL")
        == "https://hydroportal.cuahsi.org/x.asmx"
    )
    with pytest.raises(ValueError, match="HTTPS"):
        cuahsi._public_service_url("http://hydroportal.cuahsi.org/x.asmx")
    with pytest.raises(ValueError, match="outside"):
        cuahsi._public_service_url("https://example.com/x.asmx")


def test_retrieve_values_parses_waterml_datetime_and_value_attributes(monkeypatch):
    monkeypatch.setattr(
        cuahsi.socket,
        "getaddrinfo",
        lambda *_: [(None, None, None, None, ("8.8.8.8", 0))],
    )

    class Response:
        content = b"""<string xmlns="http://www.cuahsi.org/his/1.1/ws/">&lt;timeSeriesResponse&gt;
        &lt;value dateTime=\"2000-01-01T00:00:00\" dateValue=\"2.5\" /&gt;
        &lt;value dateTime=\"2000-02-01T00:00:00\" dateValue=\"3.5\" /&gt;
        &lt;/timeSeriesResponse&gt;</string>"""

        def raise_for_status(self):
            pass

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params):
            assert url == "https://hydroportal.cuahsi.org/NWIS/cuahsi_1_1.asmx/GetValues"
            assert params["location"] == "NWIS:site"
            assert params["variable"] == "NWIS:00060"
            return Response()

    monkeypatch.setattr(cuahsi.httpx, "AsyncClient", Client)
    dates, values = asyncio.run(
        cuahsi.retrieve_values(
            "https://hydroportal.cuahsi.org/NWIS/cuahsi_1_1.asmx?WSDL",
            "NWIS:site",
            "NWIS:00060",
            "2000-01-01",
            "2000-12-31",
        )
    )
    assert dates == ["2000-01-01T00:00:00", "2000-02-01T00:00:00"]
    assert values == [2.5, 3.5]


def test_cuahsi_search_api_rejects_invalid_bounds():
    async def send():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post(
                "/api/cuahsi/search",
                json={
                    "bounds": [3, 0, -3, 1],
                    "start": "2000-01-01",
                    "end": "2025-01-01",
                    "keyword": "discharge",
                },
            )

    response = asyncio.run(send())
    assert response.status_code == 422


def test_cuahsi_analysis_returns_monthly_station_result(monkeypatch):
    async def fake_search(*_args):
        return [{
            "id": "network:site:series",
            "site": "River gauge",
            "location": "network:site",
            "variable": "Streamflow",
            "variable_code": "network:flow",
            "unit": "m^3/s",
            "start": "2000-01-01",
            "end": "2002-12-31",
            "latitude": -13.0,
            "longitude": -55.0,
            "service": "network",
            "service_url": "https://hydroportal.cuahsi.org/service.asmx",
            "organization": "Water agency",
            "value_count": 36,
        }]

    async def fake_retrieve(*_args):
        dates, values = [], []
        for year in range(2000, 2003):
            for month in range(1, 13):
                dates.append(f"{year}-{month:02d}-{monthrange(year, month)[1]:02d}")
                values.append(float(year - 2000 + month / 12))
        return dates, values

    monkeypatch.setattr("api.app.main.search_series", fake_search)
    monkeypatch.setattr("api.app.main.retrieve_values", fake_retrieve)

    async def send():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post(
                "/api/cuahsi/analyze",
                json={
                    "bounds": [-60, -20, -45, 0],
                    "start": "2000-01-01",
                    "end": "2002-12-31",
                    "keyword": "Discharge, stream",
                    "series_id": "network:site:series",
                },
            )

    response = asyncio.run(send())
    assert response.status_code == 200
    result = response.json()
    assert result["source"] == "CUAHSI HydroClient · Water agency"
    assert result["unit"] == "m^3/s"
    assert result["metadata"]["n_months"] == 36
    assert result["metadata"]["series_id"] == "network:site:series"
    assert "one station" in result["caveats"][0]
