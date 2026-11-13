import asyncio

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from api.app.external_series import analyze_monthly_observations, parse_csv_series
from api.app.main import app


def test_external_daily_observations_are_monthly_aggregated_and_analyzed():
    months = np.arange("2000-01", "2005-01", dtype="datetime64[M]")
    dates = [str(day) for month in months for day in [month.astype("datetime64[D]")]]
    values = [float(index) for index in range(len(dates))]
    result = analyze_monthly_observations(dates, values)
    assert result.n_months == 60
    assert result.start == "2000-01"
    assert result.end == "2004-12"
    assert result.statistics["slope_ols"] == pytest.approx(11.5232, abs=1e-3)


def test_monthly_series_preserves_missing_months_and_requires_long_record():
    result = analyze_monthly_observations(
        ["2000-01-01", "2000-03-01"], [1.0, 3.0], minimum_months=3
    )
    assert result.dates == ["2000-01", "2000-02", "2000-03"]
    assert result.values == [1.0, None, 3.0]
    with pytest.raises(ValueError, match="At least"):
        analyze_monthly_observations(["2000-01-01"], [1.0])


def test_csv_column_selection_and_size_validation():
    dates, values = parse_csv_series("date,discharge\n2000-01-01,2.5\n", "date", "discharge")
    assert dates == ["2000-01-01"]
    assert values == [2.5]
    with pytest.raises(ValueError, match="columns"):
        parse_csv_series("time,x\n2000-01,1\n", "date", "x")


def test_external_analysis_api_returns_common_trend_contract():
    rows = ["date,value"]
    for index, date in enumerate(np.arange("2000-01", "2005-01", dtype="datetime64[M]")):
        rows.append(f"{date.astype('datetime64[D]')},{index * 0.1}")
    async def send():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/api/external/analyze", json={
                "csv_text": "\n".join(rows), "date_column": "date", "value_column": "value",
                "label": "Test station", "source": "noaa_cdo", "unit": "mm",
            })
    response = asyncio.run(send())
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "NOAA Climate Data Online"
    assert payload["trend"]["slope_ols"] == pytest.approx(1.1523, abs=1e-3)
    assert len(payload["time"]) == 60


def test_external_analysis_rejects_short_or_unknown_source():
    async def send():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            short = await client.post(
                "/api/external/analyze",
                json={
                    "csv_text": "date,value\n2000-01-01,1",
                    "date_column": "date",
                    "value_column": "value",
                    "label": "Station",
                    "source": "noaa_cdo",
                    "unit": "mm",
                },
            )
            unknown = await client.post("/api/external/analyze", json={
                "csv_text": "date,value", "date_column": "date", "value_column": "value",
                "label": "X", "source": "unknown", "unit": "mm",
            })
            return short, unknown
    short, unknown = asyncio.run(send())
    assert short.status_code == 422
    assert unknown.status_code == 422
