from fastapi.testclient import TestClient

from app.database import check_database_health
from app.main import app


def test_root_route_returns_running_message():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "BitBound Pay API is running"}


def test_database_health_is_healthy():
    health = check_database_health()

    assert health["status"] == "healthy"
