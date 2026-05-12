from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from corpus_watch.models import Asset, Household, PriceQuote, Transaction
from corpus_watch.repository import get_networth_history
from tests.conftest import CAS_DATA


def _setup(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Priya Sharma", "household_name": "Sharma Family"},
    )


def _import(client: TestClient) -> None:
    with patch("corpus_watch.ingest.cas.casparser.read_cas_pdf", return_value=CAS_DATA):
        client.post(
            "/api/import/cas",
            files={"file": ("statement.pdf", b"%PDF-fake", "application/pdf")},
            data={"password": "TESTPAN"},
        )


def _household_id(db: Session) -> str:
    return db.query(Household).first().id  # type: ignore[union-attr]


# ── Repository unit tests ─────────────────────────────────────────────────────


def test_history_empty_portfolio(db_session: object) -> None:
    db: Session = db_session  # type: ignore[assignment]
    series, asset_classes = get_networth_history(
        db, "nonexistent-household", date(2025, 1, 1), date(2025, 12, 31)
    )
    assert series == []
    assert asset_classes == []


def test_history_no_price_quotes(client: TestClient, db_session: object) -> None:
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)
    series, _ = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )
    assert series == []


def test_history_single_asset_single_date(client: TestClient, db_session: object) -> None:
    """100 units x 150 NAV on one date -> one point with correct value."""
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    db.add(
        PriceQuote(
            kind="MF", key="000001", ts=date(2025, 6, 1), price=Decimal("150.00"), source="mfapi"
        )
    )
    db.commit()

    series, asset_classes = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )

    assert len(series) == 1
    assert series[0]["date"] == "2025-06-01"
    assert float(series[0]["total"]) == pytest.approx(15000.0)
    assert float(series[0]["MF"]) == pytest.approx(15000.0)
    assert asset_classes == ["MF"]


def test_history_multiple_dates(client: TestClient, db_session: object) -> None:
    """Returns one point per date with price data."""
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    for d, price in [
        (date(2025, 5, 1), "100.00"),
        (date(2025, 6, 1), "110.00"),
        (date(2025, 7, 1), "105.00"),
    ]:
        db.add(PriceQuote(kind="MF", key="000001", ts=d, price=Decimal(price), source="mfapi"))
    db.commit()

    series, _ = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )

    assert len(series) == 3
    assert float(series[0]["total"]) == pytest.approx(10000.0)  # 100 x 100
    assert float(series[1]["total"]) == pytest.approx(11000.0)  # 100 x 110
    assert float(series[2]["total"]) == pytest.approx(10500.0)  # 100 x 105


def test_history_date_window_filters(client: TestClient, db_session: object) -> None:
    """Only dates within [start, end] are returned."""
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    for d in [date(2024, 12, 31), date(2025, 6, 1), date(2025, 12, 31), date(2026, 1, 1)]:
        db.add(PriceQuote(kind="MF", key="000001", ts=d, price=Decimal("100.00"), source="mfapi"))
    db.commit()

    series, _ = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )

    dates = [p["date"] for p in series]
    assert "2024-12-31" not in dates
    assert "2026-01-01" not in dates
    assert "2025-06-01" in dates
    assert "2025-12-31" in dates


def test_history_units_accumulate_after_purchase(
    client: TestClient, db_session: object
) -> None:
    """Second purchase mid-period increases units_held for subsequent dates."""
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    asset = db.query(Asset).filter_by(scheme_code="000001").first()
    db.add(
        Transaction(
            asset_id=asset.id,
            ts=date(2025, 6, 1),
            type="PURCHASE",
            units=Decimal("50"),
            amount=Decimal("5500"),
            identity_key="second-buy",
        )
    )
    db.commit()

    for d, price in [(date(2025, 5, 15), "100.00"), (date(2025, 6, 15), "100.00")]:
        db.add(PriceQuote(kind="MF", key="000001", ts=d, price=Decimal(price), source="mfapi"))
    db.commit()

    series, _ = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )

    assert len(series) == 2
    assert float(series[0]["total"]) == pytest.approx(10000.0)  # 100 units before second buy
    assert float(series[1]["total"]) == pytest.approx(15000.0)  # 150 units after second buy


def test_history_units_drop_after_sell(client: TestClient, db_session: object) -> None:
    """Redemption reduces units_held for dates after the sell."""
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    asset = db.query(Asset).filter_by(scheme_code="000001").first()
    db.add(
        Transaction(
            asset_id=asset.id,
            ts=date(2025, 7, 1),
            type="REDEMPTION",
            units=Decimal("-40"),
            amount=Decimal("4200"),
            identity_key="partial-redeem",
        )
    )
    db.commit()

    for d, price in [(date(2025, 6, 15), "100.00"), (date(2025, 7, 15), "100.00")]:
        db.add(PriceQuote(kind="MF", key="000001", ts=d, price=Decimal(price), source="mfapi"))
    db.commit()

    series, _ = get_networth_history(
        db, _household_id(db), date(2025, 1, 1), date(2025, 12, 31)
    )

    assert float(series[0]["total"]) == pytest.approx(10000.0)  # 100 units before sell
    assert float(series[1]["total"]) == pytest.approx(6000.0)   # 60 units after sell


# ── API endpoint tests ────────────────────────────────────────────────────────


def test_history_endpoint_before_setup_returns_400(client: TestClient) -> None:
    resp = client.get("/api/networth/history")
    assert resp.status_code == 400


def test_history_endpoint_empty(client: TestClient) -> None:
    _setup(client)
    resp = client.get("/api/networth/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["series"] == []
    assert body["asset_classes"] == []


def test_history_endpoint_with_data(client: TestClient, db_session: object) -> None:
    db: Session = db_session  # type: ignore[assignment]
    _setup(client)
    _import(client)

    db.add(
        PriceQuote(
            kind="MF", key="000001", ts=date(2025, 6, 1), price=Decimal("150.00"), source="mfapi"
        )
    )
    db.commit()

    resp = client.get("/api/networth/history?start=2025-01-01&end=2025-12-31")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["series"]) == 1
    assert body["asset_classes"] == ["MF"]
    assert float(body["series"][0]["total"]) == pytest.approx(15000.0)
