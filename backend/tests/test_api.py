from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "PromptGuard-KVKK API",
        "version": "0.1.0",
    }


def test_cors_allows_explicit_loopback_development_origin() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://127.0.0.1:3100"},
        )

    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3100"


def test_analyze_placeholder_for_valid_prompt() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": "A valid prompt"})

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "analyzed"
    assert body["entity_count"] == 0
    assert body["entities"] == []
    assert body["analysis_id"]
    assert body["risk"] == {"score": 0, "level": "LOW", "decision": "ALLOW"}
    assert body["risk_factors"] == []
    assert body["sanitized_prompt"] == "A valid prompt"


def test_analyze_rejects_empty_prompt() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": "   "})

    assert response.status_code == 422


def test_analyze_rejects_oversized_prompt() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": "x" * 10_001})

    assert response.status_code == 422


def test_analyze_returns_normalized_entities() -> None:
    prompt = "Ahmet Yılmaz için user@example.com adresine yazın."
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": prompt})

    body = response.json()
    assert response.status_code == 200
    assert body["entity_count"] == 2
    assert [entity["type"] for entity in body["entities"]] == ["PERSON", "EMAIL"]
    for entity in body["entities"]:
        assert prompt[entity["start"] : entity["end"]] == entity["text"]
        assert entity["category"]
        assert entity["risk_contribution"] >= 0
    assert body["risk"]["level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert "[EMAIL]" in body["sanitized_prompt"]
