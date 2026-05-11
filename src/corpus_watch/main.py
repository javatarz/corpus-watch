from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from corpus_watch.routers import health, import_, networth, setup


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    from corpus_watch.settings import settings

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{settings.db_path}")
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Migrations also seed AssetClass rows (see 0001_initial.py).
    _run_migrations()
    yield


app = FastAPI(title="corpus-watch", lifespan=lifespan)
app.include_router(health.router)
app.include_router(setup.router)
app.include_router(import_.router)
app.include_router(networth.router)
