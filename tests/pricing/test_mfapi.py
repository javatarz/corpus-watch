import json
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from corpus_watch.database import Base
from corpus_watch.models import AssetClass, PriceQuote, RefreshLog
from corpus_watch.pricing.mfapi import (
    _parse_date,
    _start_date,
    _upsert_quotes,
    fetch_scheme,
)
from corpus_watch.repository import get_stale_scheme_codes

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_NAV_DATA = [
    {"date": "05-01-2024", "nav": "108.29340"},
    {"date": "04-01-2024", "nav": "108.30680"},
    {"date": "03-01-2024", "nav": "N.A."},
    {"date": "02-01-2024", "nav": ""},
    {"date": "01-01-2024", "nav": "108.30200"},
]


def _mock_urlopen(data: list[dict[str, str]]) -> MagicMock:
    body = json.dumps({"status": "SUCCESS", "meta": {}, "data": data}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    ctx = MagicMock()
    ctx.__enter__ = lambda s: mock_resp
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


@pytest.fixture()
def db() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    session = factory()
    session.add(AssetClass(code="MF", name="Mutual Funds", kind="fund"))
    session.commit()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


def test_parse_date() -> None:
    assert _parse_date("05-01-2024") == date(2024, 1, 5)


def test_upsert_quotes_filters_invalid(db: Session) -> None:
    _upsert_quotes(db, "000001", _SAMPLE_NAV_DATA)
    db.commit()
    rows = db.query(PriceQuote).filter_by(key="000001").all()
    # "N.A." and "" entries are skipped
    assert len(rows) == 3
    prices = {r.ts: r.price for r in rows}
    assert prices[date(2024, 1, 5)] == Decimal("108.29340")
    assert prices[date(2024, 1, 4)] == Decimal("108.30680")
    assert prices[date(2024, 1, 1)] == Decimal("108.30200")


def test_upsert_quotes_idempotent(db: Session) -> None:
    _upsert_quotes(db, "000001", _SAMPLE_NAV_DATA)
    db.commit()
    _upsert_quotes(db, "000001", _SAMPLE_NAV_DATA)
    db.commit()
    count = db.query(PriceQuote).filter_by(key="000001").count()
    assert count == 3


def test_fetch_scheme_success(db: Session) -> None:
    mock = _mock_urlopen(_SAMPLE_NAV_DATA)
    with patch("corpus_watch.pricing.mfapi.urllib.request.urlopen", return_value=mock):
        fetch_scheme(db, "000001", date(2024, 1, 1))

    log = db.query(RefreshLog).filter_by(scheme_code="000001").first()
    assert log is not None
    assert log.status == "success"
    assert log.error is None
    assert db.query(PriceQuote).filter_by(key="000001").count() == 3


def test_fetch_scheme_error_logged(db: Session) -> None:
    import urllib.error

    with patch(
        "corpus_watch.pricing.mfapi.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        fetch_scheme(db, "000001", date(2024, 1, 1))

    log = db.query(RefreshLog).filter_by(scheme_code="000001").first()
    assert log is not None
    assert log.status == "error"
    assert "connection refused" in (log.error or "")
    assert db.query(PriceQuote).filter_by(key="000001").count() == 0


def test_start_date_no_prior_log(db: Session) -> None:
    fallback = date(2020, 1, 1)
    assert _start_date(db, "000001", fallback) == fallback


def test_start_date_gap_only(db: Session) -> None:
    finished = datetime(2024, 1, 5, 12, 0, 0)
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="000001",
            started_at=finished,
            finished_at=finished,
            status="success",
        )
    )
    db.commit()
    result = _start_date(db, "000001", date(2020, 1, 1))
    assert result == date(2024, 1, 6)


def test_get_stale_scheme_codes_fresh(db: Session) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="000001",
            started_at=now,
            finished_at=now,
            status="success",
        )
    )
    db.commit()
    assert get_stale_scheme_codes(db, ["000001"]) == []


def test_get_stale_scheme_codes_stale(db: Session) -> None:
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
    assert get_stale_scheme_codes(db, ["000001"]) == ["000001"]


def test_get_stale_scheme_codes_never_refreshed(db: Session) -> None:
    assert get_stale_scheme_codes(db, ["000001"]) == ["000001"]


def test_partial_failure_only_failed_retried(db: Session) -> None:
    """After a failed refresh, the failed scheme appears stale; the successful one does not."""
    now = datetime.now(UTC).replace(tzinfo=None)
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="111111",
            started_at=now,
            finished_at=now,
            status="success",
        )
    )
    db.add(
        RefreshLog(
            source="mfapi",
            scheme_code="222222",
            started_at=now,
            finished_at=now,
            status="error",
        )
    )
    db.commit()
    stale = get_stale_scheme_codes(db, ["111111", "222222"])
    assert stale == ["222222"]
