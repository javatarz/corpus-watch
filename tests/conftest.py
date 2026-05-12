from collections.abc import Generator
from unittest.mock import patch

import pytest
from casparser.enums import CASFileType, FileType, TransactionType
from casparser.types import (
    CASData,
    Folio,
    InvestorInfo,
    Scheme,
    SchemeValuation,
    StatementPeriod,
    TransactionData,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from corpus_watch.database import Base, get_db
from corpus_watch.main import app
from corpus_watch.models import AssetClass

# ---------------------------------------------------------------------------
# Fixture CAS data — typed CASData object matching casparser 0.8+ output
# ---------------------------------------------------------------------------
CAS_DATA = CASData(
    statement_period=StatementPeriod(**{"from": "2024-01-01", "to": "2024-12-31"}),
    investor_info=InvestorInfo(name="Test User", email="test@example.com", address="", mobile=""),
    cas_type=CASFileType.DETAILED,
    file_type=FileType.CAMS,
    folios=[
        Folio(
            folio="12345678/89",
            amc="Test AMC",
            PAN="XXXXX1234X",
            KYC="OK",
            PANKYC="OK",
            schemes=[
                Scheme(
                    scheme="Test MF Direct Growth",
                    isin="INF123456789",
                    amfi="000001",
                    advisor="",
                    rta_code="TEST",
                    rta="CAMS",
                    type="EQUITY",
                    nominees=[],
                    open=0.0,
                    close=100.0,
                    close_calculated=100.0,
                    valuation=SchemeValuation(date="2024-12-31", nav=123.456, value=12345.60, cost=10000.00),
                    transactions=[
                        TransactionData(
                            date="2024-01-15",
                            description="Purchase",
                            amount=10000.00,
                            units=100.0,
                            nav=100.0,
                            balance=100.0,
                            type=TransactionType.PURCHASE,
                            dividend_rate=None,
                        )
                    ],
                )
            ],
        )
    ],
)


@pytest.fixture()
def test_engine() -> Any:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def db_session(test_engine: Any) -> Generator[Session]:
    factory = sessionmaker(bind=test_engine, autoflush=False)
    db = factory()
    db.add(AssetClass(code="MF", name="Mutual Funds", kind="fund"))
    db.commit()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(test_engine: Any, db_session: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    with (
        patch("corpus_watch.main._run_migrations"),
        patch("corpus_watch.database.engine", test_engine),
    ):
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()
