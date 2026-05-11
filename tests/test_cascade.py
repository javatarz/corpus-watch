from datetime import date

from sqlalchemy.orm import Session

from corpus_watch.models import Account, Asset, Individual, Transaction
from corpus_watch.repository import (
    create_household,
    folio_hash,
    get_or_create_account,
    get_or_create_asset,
    upsert_transaction,
)


def test_cascade_delete_household(db_session: Session) -> None:
    household = create_household(db_session, "Test Family", "Test User")
    individual = household.individuals[0]
    account = get_or_create_account(db_session, individual.id, "CAMS", folio_hash("12345"))
    asset = get_or_create_asset(db_session, account.id, "000001", "Test MF")
    upsert_transaction(
        db_session,
        asset.id,
        {
            "date": date(2024, 1, 15),
            "type": "PURCHASE",
            "units": None,
            "amount": None,
            "identity_key": "abc123",
        },
    )
    db_session.commit()

    assert db_session.query(Individual).count() == 1
    assert db_session.query(Account).count() == 1
    assert db_session.query(Asset).count() == 1
    assert db_session.query(Transaction).count() == 1

    db_session.delete(household)
    db_session.commit()

    assert db_session.query(Individual).count() == 0
    assert db_session.query(Account).count() == 0
    assert db_session.query(Asset).count() == 0
    assert db_session.query(Transaction).count() == 0
