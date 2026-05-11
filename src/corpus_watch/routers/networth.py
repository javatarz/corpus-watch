from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from corpus_watch.database import get_db
from corpus_watch.repository import get_household, get_networth

router = APIRouter()


@router.get("/api/networth")
def networth(db: Session = Depends(get_db)) -> dict[str, object]:
    household = get_household(db)
    if household is None:
        raise HTTPException(400, "Not configured")
    total, as_of = get_networth(db, household.id)
    return {
        "total": str(total),
        "currency": household.base_currency,
        "as_of": as_of.isoformat() if as_of else None,
    }
