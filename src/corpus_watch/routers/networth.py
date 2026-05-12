from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from corpus_watch.database import get_db
from corpus_watch.pricing.mfapi import refresh_stale_schemes
from corpus_watch.repository import (
    get_household,
    get_last_refresh_datetime,
    get_networth,
    get_networth_history,
    get_portfolio_scheme_codes,
    get_stale_scheme_codes,
)

router = APIRouter()


@router.get("/api/networth")
def networth(background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, object]:
    household = get_household(db)
    if household is None:
        raise HTTPException(400, "Not configured")

    scheme_codes = get_portfolio_scheme_codes(db, household.id)
    stale = get_stale_scheme_codes(db, scheme_codes)
    if stale:
        background_tasks.add_task(refresh_stale_schemes, stale)

    total, as_of = get_networth(db, household.id)
    last_refreshed = get_last_refresh_datetime(db, scheme_codes)

    return {
        "total": str(total),
        "currency": household.base_currency,
        "as_of": as_of.isoformat() if as_of else None,
        "refreshing": bool(stale),
        "last_refreshed": last_refreshed.isoformat() if last_refreshed else None,
    }


@router.get("/api/networth/history")
def networth_history(
    start: date = Query(default=None),
    end: date = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    household = get_household(db)
    if household is None:
        raise HTTPException(400, "Not configured")

    today = date.today()
    resolved_end = end if end is not None else today
    resolved_start = start if start is not None else resolved_end - timedelta(days=365)

    series, asset_classes = get_networth_history(db, household.id, resolved_start, resolved_end)
    return {"series": series, "asset_classes": asset_classes}
