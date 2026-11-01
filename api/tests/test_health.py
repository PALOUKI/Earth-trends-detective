from api.app.main import app, health


def test_health_reports_service_status() -> None:
    assert app.title == "Earth Trends Detective"
    assert health() == {"status": "ok"}
