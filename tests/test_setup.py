from starlette.testclient import TestClient


def test_setup_not_configured(client: TestClient) -> None:
    resp = client.get("/api/setup")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_setup_create(client: TestClient) -> None:
    resp = client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Sharma Family"


def test_setup_configured(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )
    resp = client.get("/api/setup")
    assert resp.json()["configured"] is True
    assert resp.json()["household_name"] == "Sharma Family"


def test_setup_duplicate_rejected(client: TestClient) -> None:
    payload = {"individual_name": "A", "household_name": "A Family"}
    client.post("/api/setup", json=payload)
    resp = client.post("/api/setup", json=payload)
    assert resp.status_code == 400
