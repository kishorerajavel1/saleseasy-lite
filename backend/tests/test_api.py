import json

import pytest
from fastapi.testclient import TestClient

from main import create_app
from tests.doubles import ScriptedLLM, configured_settings


def client(**settings):
    return TestClient(create_app(configured_settings(**settings), ScriptedLLM()))


def test_public_contract_and_metadata():
    response = client().post("/analyze", json={"text": "Metro Fresh cola is out of stock."})
    assert response.status_code == 200
    assert set(response.json()) == {
        "issue_category",
        "urgency",
        "evidence",
        "recommended_next_action",
        "missing_information",
        "needs_human_review",
        "review_reason",
    }
    assert response.headers["X-Analysis-Model"] == "test-boundary"
    assert response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "body",
    [
        {"text": ""},
        {"text": "   "},
        {"text": "\u200b"},
        {"text": "x" * 2001},
        {"text": 123},
        {"text": "hello", "force_failure": True},
        {"text": "hello\u0000there"},
    ],
)
def test_invalid_inputs(body):
    response = client().post("/analyze", json=body)
    assert response.status_code == 422
    if isinstance(response.json()["detail"], list):
        assert all("input" not in detail for detail in response.json()["detail"])


def test_streamed_body_cap_and_invalid_json():
    with client(max_body_bytes=512, rate_limit_per_ip=20) as session:
        response = session.post("/analyze", content=iter([b"x" * 300, b"x" * 300]))
        assert response.status_code == 413
        assert (
            session.post(
                "/analyze", content="{bad", headers={"Content-Type": "application/json"}
            ).status_code
            == 422
        )


def test_rate_limit_cannot_be_bypassed_by_forwarded_headers():
    with client(rate_limit_per_ip=1) as session:
        assert session.post("/analyze", json={"text": "hello"}).status_code == 200
        response = session.post(
            "/analyze", json={"text": "hello"}, headers={"X-Forwarded-For": "1.2.3.4"}
        )
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"
        assert session.get("/health").status_code == 200


def test_provider_failure_returns_an_error_without_analysis():
    with TestClient(create_app(configured_settings(), ScriptedLLM(TimeoutError()))) as session:
        response = session.post("/analyze", json={"text": "Customer unwell after juice."})
        assert response.status_code == 504
        assert response.json()["code"] == "analysis_timeout"
        assert "urgency" not in response.json()
        assert "manual review" in response.json()["detail"]
        assert response.headers["X-Request-ID"]


def test_health_does_not_call_provider_and_headers_protect_html():
    with TestClient(create_app(configured_settings(), ScriptedLLM())) as session:
        response = session.get("/health")
        assert response.json()["live_model_checked"] is False
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert session.app.state.analysis_service.llm.calls == 0
        output = session.post("/analyze", json={"text": "<script>alert('hello')</script>"})
        assert output.headers["Content-Type"].startswith("application/json")
        json.dumps(output.json())


def test_irrelevant_message_is_a_benign_success_response():
    response = client().post("/analyze", json={"text": "Hi"})
    assert response.status_code == 200
    assert response.json() == {
        "issue_category": "other",
        "urgency": "low",
        "evidence": [{"source": "field_update", "reference": "Hi", "verified": False}],
        "recommended_next_action": "no_action_needed",
        "missing_information": [],
        "needs_human_review": False,
        "review_reason": None,
    }
