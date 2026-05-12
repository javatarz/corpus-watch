from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from corpus_watch.models import PriceQuote, RefreshLog
from tests.conftest import CAS_DATA


def _do_setup(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )


def _do_import(client: TestClient) -> None:
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )


def test_networth_before_setup_returns_400(client: TestClient) -> None:
    resp = client.get("/api/networth")
    assert resp.status_code == 400


def test_networth_before_import(client: TestClient) -> None:
    _do_setup(client)
    resp = client.get("/api/networth")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == "0"
    assert body["currency"] == "INR"
    assert body["as_of"] is None
    assert body["refreshing"] is False
    assert body["last_refreshed"] is None


def test_networth_fallback_to_last_value(client: TestClient) -> None:
    """No PriceQuote present -> falls back to CAS last_value."""
    _do_setup(client)
    _do_import(client)
    resp = client.get("/api/networth")
    body = resp.json()
    assert body["as_of"] == "2024-12-31"
    assert float(body["total"]) == pytest.approx(12345.60)
    assert body["refreshing"] is True
    assert body["last_refreshed"] is None


def test_networth_live_nav(client: TestClient, db_session: object) -> None:
    """PriceQuote present: uses close_units x quote.price."""
    from sqlalchemy.orm import Session

    db: Session = db_session  # type: ignore[assignment]
    _do_setup(client)
    _do_import(client)

    # 100 close_units x 150.00 NAV = 15000.00
    db.add(
        PriceQuote(
            kind="MF",
            key="000001",
            ts=date(2026, 5, 12),
            price=Decimal("150.00"),
            source="mfapi",
        )
    )
    # Also seed a fresh RefreshLog so refreshing=False
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="000001",
            started_at=datetime.now(UTC).replace(tzinfo=None),
            finished_at=datetime.now(UTC).replace(tzinfo=None),
            status="success",
        )
    )
    db.commit()

    resp = client.get("/api/networth")
    body = resp.json()
    assert float(body["total"]) == pytest.approx(15000.00)
    assert body["as_of"] == "2026-05-12"
    assert body["refreshing"] is False
    assert body["last_refreshed"] is not None


def test_networth_stale_triggers_refresh(client: TestClient, db_session: object) -> None:
    """RefreshLog older than 24h -> refreshing=True."""
    from sqlalchemy.orm import Session

    db: Session = db_session  # type: ignore[assignment]
    _do_setup(client)
    _do_import(client)

    stale_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=25)
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="000001",
            started_at=stale_time,
            finished_at=stale_time,
            status="success",
        )
    )
    db.commit()

    resp = client.get("/api/networth")
    body = resp.json()
    assert body["refreshing"] is True
