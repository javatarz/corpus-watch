import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corpus_watch.database import Base, DecimalString


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Household(Base):
    __tablename__ = "households"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_currency: Mapped[str] = mapped_column(String, default="INR")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    individuals: Mapped[list[Individual]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )


class Individual(Base):
    __tablename__ = "individuals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(
        String, ForeignKey("households.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    household: Mapped[Household] = relationship(back_populates="individuals")
    accounts: Mapped[list[Account]] = relationship(
        back_populates="individual", cascade="all, delete-orphan"
    )


class AssetClass(Base):
    __tablename__ = "asset_classes"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    individual_id: Mapped[str] = mapped_column(
        String, ForeignKey("individuals.id", ondelete="CASCADE")
    )
    asset_class_code: Mapped[str] = mapped_column(String, ForeignKey("asset_classes.code"))
    broker: Mapped[str] = mapped_column(String, nullable=False)
    account_number_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    individual: Mapped[Individual] = relationship(back_populates="accounts")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id", ondelete="CASCADE"))
    scheme_code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_value: Mapped[Decimal | None] = mapped_column(DecimalString, nullable=True)
    last_value_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    close_units: Mapped[Decimal | None] = mapped_column(DecimalString, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    account: Mapped[Account] = relationship(back_populates="assets")
    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("asset_id", "identity_key"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    asset_id: Mapped[str] = mapped_column(String, ForeignKey("assets.id", ondelete="CASCADE"))
    ts: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    units: Mapped[Decimal | None] = mapped_column(DecimalString, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(DecimalString, nullable=True)
    identity_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    asset: Mapped[Asset] = relationship(back_populates="transactions")


class PriceQuote(Base):
    __tablename__ = "price_quotes"
    __table_args__ = (UniqueConstraint("kind", "key", "ts", "source"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[Decimal] = mapped_column(DecimalString, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)


class RefreshLog(Base):
    __tablename__ = "refresh_log"
    __table_args__ = (Index("ix_refresh_log_scheme_finished", "scheme_code", "finished_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String, nullable=False)
    scheme_code: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
