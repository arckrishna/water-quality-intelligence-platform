from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"
    assert "message" in data


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_summary_endpoint():
    response = client.get("/api/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_records"] > 0
    assert data["total_states"] > 0
    assert data["total_districts"] > 0
    assert data["total_parameters"] > 0


def test_states_endpoint():
    response = client.get("/api/states?limit=5")

    assert response.status_code == 200

    data = response.json()

    assert len(data["data"]) <= 5

    if data["data"]:
        assert "state_name" in data["data"][0]
        assert "total_records" in data["data"][0]


def test_parameters_endpoint():
    response = client.get("/api/parameters")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] > 0

    assert "quality_parameter" in data["data"][0]
    assert "total_records" in data["data"][0]


def test_years_endpoint():
    response = client.get("/api/years")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] > 0

    assert "year" in data["data"][0]
    assert "total_records" in data["data"][0]


def test_districts_endpoint():
    response = client.get("/api/districts?limit=5")

    assert response.status_code == 200

    data = response.json()

    assert len(data["data"]) <= 5

    if data["data"]:
        assert "district_name" in data["data"][0]
        assert "state_name" in data["data"][0]


def test_invalid_job_returns_404():
    response = client.get(
        "/api/pipeline/status/nonexistent-job-id"
    )

    assert response.status_code == 404