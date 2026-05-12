import json
import urllib.error
import urllib.request
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from corpus_watch.database import SessionLocal
from corpus_watch.models import PriceQuote, RefreshLog

_BASE = "https://api.mfapi.in/mf"
_TTL_HOURS = 24


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%d-%m-%Y").date()


def _fetch_nav_data(scheme_code: str, start_date: date) -> list[dict[str, str]]:
    url = f"{_BASE}/{scheme_code}?startDate={start_date.isoformat()}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        body: dict[str, object] = json.loads(resp.read())
    if body.get("status") != "SUCCESS":
        raise ValueError(f"mfapi status {body.get('status')} for scheme {scheme_code}")
    return body["data"]  # type: ignore[return-value]


def _upsert_quotes(db: Session, scheme_code: str, data: list[dict[str, str]]) -> None:
    rows = [
        {
            "id": str(uuid.uuid4()),
            "kind": "MF",
            "key": scheme_code,
            "ts": _parse_date(item["date"]),
            "price": str(Decimal(item["nav"])),
            "source": "mfapi",
        }
        for item in data
        if item.get("nav") and item["nav"] not in ("N.A.", "")
    ]
    if not rows:
        return
    stmt = sqlite_insert(PriceQuote).values(rows).on_conflict_do_nothing()
    db.execute(stmt)


def _last_success(db: Session, scheme_code: str) -> RefreshLog | None:
    return (
        db.query(RefreshLog)
        .filter_by(source="mfapi", scheme_code=scheme_code, status="success")
        .order_by(RefreshLog.finished_at.desc())
        .first()
    )


def _start_date(db: Session, scheme_code: str, fallback: date) -> date:
    """Start date for a gap-only fetch: day after last success, or fallback."""
    log = _last_success(db, scheme_code)
    if log and log.finished_at:
        return log.finished_at.date() + timedelta(days=1)
    return fallback


def fetch_scheme(db: Session, scheme_code: str, start_date: date) -> None:
    """Fetch NAV history for one scheme from start_date. Writes one RefreshLog row."""
    log = RefreshLog(source="mfapi", scheme_code=scheme_code, started_at=_now())
    db.add(log)
    db.flush()
    try:
        data = _fetch_nav_data(scheme_code, start_date)
        _upsert_quotes(db, scheme_code, data)
        log.finished_at = _now()
        log.status = "success"
    except (urllib.error.URLError, ValueError, KeyError) as exc:
        log.finished_at = _now()
        log.status = "error"
        log.error = str(exc)
    db.commit()


def backfill_scheme(scheme_code: str, earliest_txn_date: date) -> None:
    """Background task: backfill full NAV history for one scheme after CAS import."""
    db = SessionLocal()
    try:
        start = _start_date(db, scheme_code, earliest_txn_date)
        if start > date.today():
            return
        fetch_scheme(db, scheme_code, start)
    finally:
        db.close()


def refresh_stale_schemes(stale_scheme_codes: list[str]) -> None:
    """Background task: fetch gap NAVs for schemes that are stale (>24h)."""
    db = SessionLocal()
    try:
        today = date.today()
        for scheme_code in stale_scheme_codes:
            yesterday = today - timedelta(days=1)
            start = _start_date(db, scheme_code, yesterday)
            if start > today:
                continue
            fetch_scheme(db, scheme_code, start)
    finally:
        db.close()
