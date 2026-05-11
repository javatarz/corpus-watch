from decimal import Decimal

from sqlalchemy.orm import Session

from corpus_watch.repository import (
    create_household,
    folio_hash,
    get_networth,
    get_or_create_account,
    get_or_create_asset,
)


def test_decimal_precision_round_trip(db_session: Session) -> None:
    household = create_household(db_session, "Test Family", "Test User")
    individual = household.individuals[0]
    account = get_or_create_account(db_session, individual.id, "CAMS", folio_hash("12345"))

    asset = get_or_create_asset(db_session, account.id, "000001", "Test MF")
    asset.last_value = Decimal("0.1") + Decimal("0.2")
    db_session.commit()

    db_session.expire(asset)
    db_session.refresh(asset)

    assert asset.last_value == Decimal("0.3")


def test_networth_sums_assets(db_session: Session) -> None:
    household = create_household(db_session, "Test Family", "Test User")
    individual = household.individuals[0]

    for i, value in enumerate(["10000.50", "20000.25"]):
        account = get_or_create_account(db_session, individual.id, "CAMS", folio_hash(str(i)))
        asset = get_or_create_asset(db_session, account.id, f"scheme_{i}", f"Fund {i}")
        asset.last_value = Decimal(value)
        db_session.flush()

    db_session.commit()
    total, _ = get_networth(db_session, household.id)
    assert total == Decimal("30000.75")
