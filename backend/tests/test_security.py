from app.security import valid_api_key
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security import ProductionSecurityMiddleware


def test_api_key_comparison_fails_closed():
    assert valid_api_key(None, "expected") is False
    assert valid_api_key("provided", None) is False
    assert valid_api_key("wrong", "expected") is False
    assert valid_api_key("expected", "expected") is True


def test_production_middleware_authenticates_and_throttles():
    app = FastAPI()
    app.add_middleware(ProductionSecurityMiddleware, production=True, api_key="x" * 24, requests_per_minute=1)

    @app.get("/private")
    def private():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/private").status_code == 401
    assert client.get("/private", headers={"X-API-Key": "x" * 24}).status_code == 200
    response = client.get("/private", headers={"X-API-Key": "x" * 24})
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_health_remains_public_in_production():
    app = FastAPI()
    app.add_middleware(ProductionSecurityMiddleware, production=True, api_key="x" * 24, requests_per_minute=1)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    assert TestClient(app).get("/api/health").status_code == 200
