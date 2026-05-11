from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import CAS_DATA


def test_networth_before_setup_returns_400(client: TestClient) -> None:
    resp = client.get("/api/networth")
    assert resp.status_code == 400


def test_networth_before_import(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )
    resp = client.get("/api/networth")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == "0"
    assert body["currency"] == "INR"
    assert body["as_of"] is None


def test_networth_after_import(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )
    resp = client.get("/api/networth")
    body = resp.json()
    assert body["as_of"] == "2024-12-31"
    assert float(body["total"]) == pytest.approx(12345.60)
