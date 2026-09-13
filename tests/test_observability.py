from fastapi.testclient import TestClient

from app.main import app


def test_prometheus_endpoint_reports_route_status_and_latency():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.get("/internal/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert 'route="/health",status="200"' in response.text
    assert "http_request_duration_seconds_sum" in response.text
