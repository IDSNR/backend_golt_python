from fastapi.testclient import TestClient

from app.main import app
from conftest import auth_headers

client = TestClient(app)


def test_wallet_balance_returns_zero() -> None:
    assert client.get("/wallet/balance").status_code == 401
    response = client.get("/wallet/balance", headers=auth_headers("wallet-user"))
    assert response.status_code == 200
    assert response.json() == {"balanceCents": 0}


def test_withdraw_rejects_negative_amount() -> None:
    response = client.post("/wallet/withdraw", headers=auth_headers("wallet-user"), json={"amountCents": -1})
    assert response.status_code == 422


def test_withdraw_rejects_amount_above_balance() -> None:
    response = client.post("/wallet/withdraw", headers=auth_headers("wallet-user"), json={"amountCents": 1})
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient wallet balance"
