from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from corpus_watch.database import get_db
from corpus_watch.ingest.cas import import_cas
from corpus_watch.repository import get_household, get_networth

router = APIRouter()


@router.post("/api/import/cas")
async def import_cas_endpoint(
    file: UploadFile,
    password: str = Form(default=""),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    household = get_household(db)
    if household is None:
        raise HTTPException(400, "Not configured")

    content = await file.read()

    try:
        result = import_cas(db, content, password, household)
    except Exception as exc:
        msg = str(exc).lower()
        if any(k in msg for k in ("password", "decrypt", "incorrect", "invalid")):
            raise HTTPException(400, "Incorrect password") from exc
        raise HTTPException(400, f"Could not parse CAS: {exc}") from exc

    total, as_of = get_networth(db, household.id)
    return {
        "imported": result.imported,
        "skipped": result.skipped,
        "total": str(total),
        "currency": household.base_currency,
        "as_of": as_of.isoformat() if as_of else None,
    }
