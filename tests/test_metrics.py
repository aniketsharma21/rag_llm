from fastapi.testclient import TestClient

from src.api import app


def test_metrics_endpoint_exposes_custom_metrics():
    with TestClient(app) as client:
        response = client.get("/metrics")

        assert response.status_code == 200
        body = response.text
        assert "rag_http_requests_total" in body
        assert "rag_http_request_duration_seconds" in body
