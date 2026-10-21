from fastapi.testclient import TestClient

from main import create_app
from tests.doubles import ScriptedLLM, configured_settings


def make_client(**overrides):
    return TestClient(create_app(configured_settings(**overrides), ScriptedLLM()))


def test_separate_frontend_origin_can_preflight_and_read_metadata():
    with make_client() as client:
        headers = {"Origin": "http://localhost:5173"}
        preflight = client.options(
            "/analyze",
            headers={
                **headers,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert preflight.status_code == 200
        response = client.post(
            "/analyze", json={"text": "City Corner juice damaged."}, headers=headers
        )
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "X-Analysis-Model" in response.headers["access-control-expose-headers"]
        assert "X-Request-ID" in response.headers["access-control-expose-headers"]


def test_unlisted_origin_does_not_receive_cors_permission():
    with make_client() as client:
        response = client.get("/health", headers={"Origin": "https://untrusted.example"})
        assert "access-control-allow-origin" not in response.headers


def test_rate_limit_errors_are_readable_by_allowed_frontend():
    with make_client(rate_limit_per_ip=1) as client:
        headers = {"Origin": "http://localhost:5173"}
        client.post("/analyze", json={"text": "hello"}, headers=headers)
        response = client.post("/analyze", json={"text": "hello"}, headers=headers)
        assert response.status_code == 429
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_inventory_endpoint_uses_the_policy_catalog():
    with make_client() as client:
        response = client.get("/inventory")
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json()[1] == {
            "id": "inv-002",
            "outlet": "Metro Fresh",
            "sku": "Cola 500ml",
            "system_stock": 48,
        }
