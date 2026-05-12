import hashlib
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import casparser
from casparser.types import CASData
from sqlalchemy.orm import Session

from corpus_watch.models import Household
from corpus_watch.repository import (
    folio_hash,
    get_or_create_account,
    get_or_create_asset,
    upsert_transaction,
)


@dataclass
class ImportResult:
    imported: int
    skipped: int


def _identity_key(
    folio: str,
    amfi: str,
    txn_date: date,
    units: Decimal | None,
    amount: Decimal | None,
) -> str:
    raw = f"{folio}:{amfi}:{txn_date.isoformat()}:{units}:{amount}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _to_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def import_cas(db: Session, file_bytes: bytes, password: str, household: Household) -> ImportResult:
    data: CASData = casparser.read_cas_pdf(io.BytesIO(file_bytes), password)

    individual = household.individuals[0]
    imported = 0
    skipped = 0

    for folio_data in data.folios:
        folio_num = folio_data.folio
        amc = folio_data.amc
        fhash = folio_hash(folio_num)

        account = get_or_create_account(db, individual.id, amc, fhash)

        for scheme in folio_data.schemes:
            amfi = scheme.amfi or scheme.isin or ""
            scheme_name = scheme.scheme

            asset = get_or_create_asset(db, account.id, amfi, scheme_name)

            asset.last_value = _to_decimal(scheme.valuation.value)
            asset.last_value_as_of = _to_date(scheme.valuation.date)

            for txn in scheme.transactions:
                txn_date = _to_date(txn.date)
                units = _to_decimal(txn.units)
                amount = _to_decimal(txn.amount)
                ikey = _identity_key(folio_num, amfi, txn_date, units, amount)

                if upsert_transaction(
                    db,
                    asset.id,
                    {
                        "date": txn_date,
                        "type": txn.type.value,
                        "units": units,
                        "amount": amount,
                        "identity_key": ikey,
                    },
                ):
                    imported += 1
                else:
                    skipped += 1

    db.commit()
    return ImportResult(imported=imported, skipped=skipped)
