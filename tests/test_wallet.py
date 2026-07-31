from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_wallet_balance_returns_zero() -> None:
    response = client.get("/wallet/balance")
    assert response.status_code == 200
    assert response.json() == {"balanceCents": 0}


def test_withdraw_rejects_negative_amount() -> None:
    response = client.post("/wallet/withdraw", json={"amountCents": -1})
    assert response.status_code == 400
    assert response.json()["detail"] == "amountCents must be a non-negative integer"
