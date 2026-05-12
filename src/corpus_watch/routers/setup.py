from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from corpus_watch.database import get_db
from corpus_watch.repository import create_household, get_household

router = APIRouter()


class SetupRequest(BaseModel):
    individual_name: str
    household_name: str


@router.get("/api/setup")
def get_setup(db: Session = Depends(get_db)) -> dict[str, object]:
    household = get_household(db)
    if household is None:
        return {"configured": False}
    return {
        "configured": True,
        "household_name": household.name,
        "individuals": [i.name for i in household.individuals],
    }


@router.post("/api/setup", status_code=201)
def post_setup(body: SetupRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if get_household(db) is not None:
        raise HTTPException(400, "Already configured")
    household = create_household(db, body.household_name, body.individual_name)
    return {"id": household.id, "name": household.name}
