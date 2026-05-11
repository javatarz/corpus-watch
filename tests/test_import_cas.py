from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import CAS_DATA


def _setup(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )


def test_import_persists_transactions(client: TestClient) -> None:
    _setup(client)
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        resp = client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] == 1
    assert body["skipped"] == 0
    assert body["as_of"] == "2024-12-31"
    assert float(body["total"]) == pytest.approx(12345.60)


def test_import_idempotent(client: TestClient) -> None:
    _setup(client)
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )
        resp = client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )
    body = resp.json()
    assert body["imported"] == 0
    assert body["skipped"] == 1
    assert float(body["total"]) == pytest.approx(12345.60)


def test_import_wrong_password_returns_400(client: TestClient) -> None:
    _setup(client)
    with patch(
        "corpus_watch.ingest.cas.casparser.read_cas_pdf",
        side_effect=Exception("incorrect password"),
    ):
        resp = client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "WRONG"},
        )
    assert resp.status_code == 400
    assert "password" in resp.json()["detail"].lower()


def test_import_requires_setup(client: TestClient) -> None:
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        resp = client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
        )
    assert resp.status_code == 400
