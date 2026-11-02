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
    catalog = _request("/api/catalog")

    assert variables.status_code == regions.status_code == suggestions.status_code == 200
    assert variables.json()[0]["id"] == "gistemp_tas_anom"
    assert "definition" in variables.json()[0]
    assert regions.json()[0]["geometry_type"] == "illustrative_rectangle"
    gpm = next(item for item in catalog.json() if item["id"] == "gpm_precipitation")
    assert suggestions.json()[0]["variable"] == "gpm_precipitation"
    assert suggestions.json()[0]["available"] is (gpm["status"] == "analysis_ready")


def test_analysis_variables_match_ready_catalog_records() -> None:
    variables = _request("/api/variables")
    catalog = _request("/api/catalog")

    assert variables.status_code == catalog.status_code == 200
    ready_ids = {
        item["id"] for item in catalog.json() if item["status"] == "analysis_ready"
    }
    assert {item["id"] for item in variables.json()} == ready_ids
    assert all(item["windows"] for item in variables.json())


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
    assert products["merra2_flux"]["status"] in {
        "acquiring",
        "series_processed",
        "analysis_ready",
    }
    assert products["gldas_noah_monthly"]["status"] in {
        "acquiring",
        "series_processed",
        "analysis_ready",
    }
    assert products["gpm_precipitation"]["unit"] == "mm/hr"
    assert products["gpm_precipitation"]["windows"] == ["full", "2010-fin", "2015-fin"]
    assert products["gpm_precipitation"]["status"] in {
        "acquiring",
        "series_processed",
        "analysis_ready",
    }
    assert products["omi_no2"]["unit"] == "molec/cm2"
    assert products["omi_no2"]["status"] in {
        "acquiring",
        "series_processed",
        "analysis_ready",
    }


def test_air_quality_suggestion_matches_omi_catalog_availability() -> None:
    response = _request("/api/suggest?theme=air")
    product_response = _request("/api/catalog")

    assert response.status_code == 200
    suggestion = response.json()[0]
    omi = next(item for item in product_response.json() if item["id"] == "omi_no2")
    assert suggestion["variable"] == "omi_no2"
    assert suggestion["available"] is (omi["status"] == "analysis_ready")
    if suggestion["available"]:
        assert "Analyze" in suggestion["message"]
    else:
        assert suggestion["message"] == omi["status_detail"]
