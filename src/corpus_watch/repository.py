import hashlib
from bisect import bisect_right
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from corpus_watch.models import (
    Account,
    Asset,
    AssetClass,
    Household,
    Individual,
    PriceQuote,
    RefreshLog,
    Transaction,
)


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
        quote = (
            db.query(PriceQuote)
            .filter_by(kind="MF", key=asset.scheme_code)
            .order_by(PriceQuote.ts.desc())
            .first()
        )
        if quote is not None and asset.close_units is not None:
            value = asset.close_units * quote.price
            nav_date: date | None = quote.ts
        elif asset.last_value is not None:
            value = asset.last_value
            nav_date = asset.last_value_as_of
        else:
            continue
        total += value
        if nav_date is not None and (as_of is None or nav_date > as_of):
            as_of = nav_date
    return total, as_of


def get_portfolio_scheme_codes(db: Session, household_id: str) -> list[str]:
    rows = (
        db.query(Asset.scheme_code)
        .join(Account)
        .join(Individual)
        .filter(Individual.household_id == household_id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_stale_scheme_codes(db: Session, scheme_codes: list[str]) -> list[str]:
    if not scheme_codes:
        return []
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=24)
    fresh = {
        row[0]
        for row in db.query(RefreshLog.scheme_code)
        .filter(
            RefreshLog.scheme_code.in_(scheme_codes),
            RefreshLog.status == "success",
            RefreshLog.finished_at > cutoff,
        )
        .distinct()
        .all()
    }
    return [sc for sc in scheme_codes if sc not in fresh]


def get_last_refresh_datetime(db: Session, scheme_codes: list[str]) -> datetime | None:
    if not scheme_codes:
        return None
    log = (
        db.query(RefreshLog)
        .filter(RefreshLog.scheme_code.in_(scheme_codes), RefreshLog.status == "success")
        .order_by(RefreshLog.finished_at.desc())
        .first()
    )
    return log.finished_at if log else None


def get_networth_history(
    db: Session, household_id: str, start: date, end: date
) -> tuple[list[dict[str, object]], list[str]]:
    """Return daily net worth series within [start, end], broken down by asset class.

    Returns (series, asset_classes) where series is a list of dicts:
      {"date": "YYYY-MM-DD", "total": Decimal, "<class_code>": Decimal, ...}
    and asset_classes is the ordered list of class codes present.
    """
    rows = (
        db.query(Asset, Account)
        .join(Account, Asset.account_id == Account.id)
        .join(Individual, Account.individual_id == Individual.id)
        .filter(Individual.household_id == household_id)
        .all()
    )
    if not rows:
        return [], []

    asset_class_by_asset: dict[str, str] = {a.id: ac.asset_class_code for a, ac in rows}
    scheme_by_asset: dict[str, str] = {a.id: a.scheme_code for a, _ in rows}
    asset_ids = list(asset_class_by_asset.keys())
    scheme_codes = list({a.scheme_code for a, _ in rows})

    # Precompute prefix-sum unit holdings per asset (sorted by txn date)
    txns = (
        db.query(Transaction)
        .filter(Transaction.asset_id.in_(asset_ids), Transaction.units.isnot(None))
        .order_by(Transaction.ts)
        .all()
    )
    txn_dates: dict[str, list[date]] = defaultdict(list)
    txn_cumulative: dict[str, list[Decimal]] = defaultdict(list)
    for txn in txns:
        prev = txn_cumulative[txn.asset_id][-1] if txn_cumulative[txn.asset_id] else Decimal(0)
        txn_dates[txn.asset_id].append(txn.ts)
        txn_cumulative[txn.asset_id].append(prev + (txn.units or Decimal(0)))

    def units_at(asset_id: str, d: date) -> Decimal:
        dates = txn_dates[asset_id]
        if not dates:
            return Decimal(0)
        idx = bisect_right(dates, d) - 1
        return txn_cumulative[asset_id][idx] if idx >= 0 else Decimal(0)

    # Load price quotes in the date window for relevant schemes
    quotes = (
        db.query(PriceQuote)
        .filter(
            PriceQuote.kind == "MF",
            PriceQuote.key.in_(scheme_codes),
            PriceQuote.ts >= start,
            PriceQuote.ts <= end,
        )
        .order_by(PriceQuote.ts)
        .all()
    )

    # Index by (scheme_code, date)
    price_index: dict[tuple[str, date], Decimal] = {(q.key, q.ts): q.price for q in quotes}
    all_dates = sorted({q.ts for q in quotes})

    seen_classes: list[str] = []
    series: list[dict[str, object]] = []

    for d in all_dates:
        by_class: dict[str, Decimal] = defaultdict(Decimal)
        for asset_id, scheme_code in scheme_by_asset.items():
            price = price_index.get((scheme_code, d))
            if price is None:
                continue
            held = units_at(asset_id, d)
            if held <= 0:
                continue
            by_class[asset_class_by_asset[asset_id]] += held * price

        if not by_class:
            continue

        for cls in by_class:
            if cls not in seen_classes:
                seen_classes.append(cls)

        total = sum(by_class.values())
        point: dict[str, object] = {"date": d.isoformat(), "total": str(total)}
        for cls, val in by_class.items():
            point[cls] = str(val)
        series.append(point)

    return series, seen_classes
