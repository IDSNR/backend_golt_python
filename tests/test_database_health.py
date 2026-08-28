from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_database_health_endpoint_returns_a_known_status() -> None:
    response = client.get('/health/database')

    assert response.status_code == 200
    assert response.json()['service'] == 'postgresql'
    assert response.json()['status'] in {'ok', 'unavailable'}