import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    # Context manager triggers the FastAPI lifespan startup logic (loads ONNX models)
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text

def test_triage_endpoint(client):
    payload = {
        "bug_id": "BUG-8921",
        "summary": "Null Pointer Exception in Auth Middleware",
        "description": "Token parser fails on missing Bearer prefix in header",
        "stacktrace": "java.lang.NullPointerException at auth.v2.TokenFilter"
    }
    
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["bug_id"] == "BUG-8921"
    assert "predicted_team" in data
    assert "confidence_score" in data
    assert isinstance(data["top_similar_historic_bugs"], list)