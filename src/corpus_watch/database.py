import sqlite3
from collections.abc import Generator
from decimal import Decimal

from sqlalchemy import String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from corpus_watch.settings import settings


class DecimalString(TypeDecorator[Decimal]):
    """Stores Decimal as TEXT in SQLite for exact precision."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: object, dialect: object) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))


class Base(DeclarativeBase):
    pass


def _make_url(path: str) -> str:
    return "sqlite://" if path == ":memory:" else f"sqlite:///{path}"


engine = create_engine(
    _make_url(settings.db_path),
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_wal(conn: sqlite3.Connection, _: object) -> None:
    conn.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
