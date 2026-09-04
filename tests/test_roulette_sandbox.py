from fastapi.testclient import TestClient

from app.main import app
from app.modules.roulette.service import roulette_sandbox_service
from conftest import auth_headers


client = TestClient(app)


def test_roulette_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ROULETTE_SANDBOX_ENABLED", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    status_response = client.get("/roulette/status")
    session_response = client.get("/roulette/session", headers=auth_headers("sandbox-disabled-user"))

    assert status_response.status_code == 200
    assert status_response.json()["enabled"] is False
    assert status_response.json()["cashValue"] is False
    assert session_response.status_code == 503


def test_roulette_cannot_be_enabled_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ROULETTE_SANDBOX_ENABLED", "true")
    monkeypatch.setenv("APP_ENV", "production")

    response = client.get("/roulette/status")

    assert response.json()["enabled"] is False
    assert response.json()["mode"] == "disabled"


def test_development_sandbox_uses_five_tiers_and_consumes_test_credit(monkeypatch) -> None:
    monkeypatch.setenv("ROULETTE_SANDBOX_ENABLED", "true")
    monkeypatch.setenv("APP_ENV", "development")
    user_id = "sandbox-five-tier-user"
    headers = auth_headers(user_id)

    for _ in range(roulette_sandbox_service.required_ad_watches):
        assert client.post("/roulette/ads/watched", headers=headers).status_code == 200

    session_response = client.get("/roulette/session", headers=headers)
    session = session_response.json()
    spin_response = client.post("/roulette/spin", headers=headers, json={"sessionId": session["sessionId"]})

    assert session_response.status_code == 200
    assert session["mode"] == "sandbox"
    assert [option["id"] for option in session["options"]] == ["common", "uncommon", "rare", "epic", "legendary"]
    assert sum(option["probability"] for option in session["options"]) == 1
    assert spin_response.status_code == 200
    assert spin_response.json()["decision"]["cashValue"] is False
    assert client.get("/roulette/ads/progress", headers=headers).json()["watched"] == 0


def test_sandbox_session_cannot_be_used_by_another_account(monkeypatch) -> None:
    monkeypatch.setenv("ROULETTE_SANDBOX_ENABLED", "true")
    monkeypatch.setenv("APP_ENV", "development")
    owner_headers = auth_headers("sandbox-session-owner")
    other_headers = auth_headers("sandbox-session-outsider")
    session = client.get("/roulette/session", headers=owner_headers).json()

    response = client.post("/roulette/spin", headers=other_headers, json={"sessionId": session["sessionId"]})

    assert response.status_code == 404
