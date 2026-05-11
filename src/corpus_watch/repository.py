import hashlib
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from corpus_watch.models import Account, Asset, AssetClass, Household, Individual, Transaction


def get_household(db: Session) -> Household | None:
    return db.query(Household).first()


def create_household(db: Session, name: str, individual_name: str) -> Household:
    household = Household(name=name)
    db.add(household)
    db.flush()
    individual = Individual(household_id=household.id, name=individual_name)
    db.add(individual)
    db.commit()
    db.refresh(household)
    return household


def ensure_asset_classes(db: Session) -> None:
    if not db.get(AssetClass, "MF"):
        db.add(AssetClass(code="MF", name="Mutual Funds", kind="fund"))
        db.commit()


def get_or_create_account(db: Session, individual_id: str, broker: str, folio_hash: str) -> Account:
    account = (
        db.query(Account)
        .filter_by(
            individual_id=individual_id,
            asset_class_code="MF",
            account_number_hash=folio_hash,
        )
        .first()
    )
    if not account:
        account = Account(
            individual_id=individual_id,
            asset_class_code="MF",
            broker=broker,
            account_number_hash=folio_hash,
        )
        db.add(account)
        db.flush()
    return account


def get_or_create_asset(db: Session, account_id: str, scheme_code: str, name: str) -> Asset:
    asset = db.query(Asset).filter_by(account_id=account_id, scheme_code=scheme_code).first()
    if not asset:
        asset = Asset(account_id=account_id, scheme_code=scheme_code, name=name)
        db.add(asset)
        db.flush()
    return asset


def upsert_transaction(db: Session, asset_id: str, txn: dict[str, object]) -> bool:
    """Returns True if inserted, False if already exists."""
    identity_key = str(txn["identity_key"])
    if db.query(Transaction).filter_by(asset_id=asset_id, identity_key=identity_key).first():
        return False
    db.add(
        Transaction(
            asset_id=asset_id,
            ts=txn["date"],
            type=str(txn["type"]),
            units=txn.get("units"),
            amount=txn.get("amount"),
            identity_key=identity_key,
        )
    )
    return True


def folio_hash(folio: str) -> str:
    return hashlib.sha256(folio.encode()).hexdigest()


def get_networth(db: Session, household_id: str) -> tuple[Decimal, date | None]:
    assets = (
        db.query(Asset)
        .join(Account)
        .join(Individual)
        .filter(Individual.household_id == household_id)
        .all()
    )
    total = Decimal("0")
    as_of: date | None = None
    for asset in assets:
        if asset.last_value is not None:
            total += asset.last_value
        if asset.last_value_as_of is not None and (as_of is None or asset.last_value_as_of > as_of):
            as_of = asset.last_value_as_of
    return total, as_of
