import asyncio

from httpx import ASGITransport, AsyncClient

from api.app.main import app


def _request(path: str):
    async def run_request():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get(path)

    return asyncio.run(run_request())


def test_health_reports_service_status() -> None:
    response = _request("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_catalog_suggestions_and_regions_have_contract_fields() -> None:
    variables = _request("/api/variables")
    regions = _request("/api/regions")
    suggestions = _request("/api/suggest?theme=water")

    assert variables.status_code == regions.status_code == suggestions.status_code == 200
    assert variables.json()[0]["id"] == "gistemp_tas_anom"
    assert "definition" in variables.json()[0]
    assert regions.json()[0]["geometry_type"] == "illustrative_rectangle"
    assert suggestions.json()[0]["available"] is False


def test_catalog_distinguishes_ready_sample_and_access_blocked_products() -> None:
    response = _request("/api/catalog")

    assert response.status_code == 200
    products = {item["id"]: item for item in response.json()}
    assert products["gistemp_tas_anom"]["status"] == "analysis_ready"
    assert products["modis_ndvi"]["short_name"] == "MOD13C2"
    assert products["modis_ndvi"]["status"] in {
        "sample_downloaded",
        "acquiring",
        "series_processed",
        "analysis_ready",
    }
    assert products["modis_ndvi"]["doi"] == "10.5067/MODIS/MOD13C2.061"
    assert products["merra2_flux"]["status"] == "blocked_eula"
