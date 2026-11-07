from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, Request
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

ROOT = Path(__file__).resolve().parent.parent


def make_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url)

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record) -> None:
        # SQLite only enforces FKs (and ON DELETE CASCADE) when asked to.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def sync_url(database_url: str) -> str:
    """Alembic runs with the sync sqlite driver; the app uses aiosqlite."""
    url = make_url(database_url)
    if url.drivername == "sqlite+aiosqlite":
        url = url.set(drivername="sqlite")
    return url.render_as_string(hide_password=False)


def run_migrations(database_url: str) -> None:
    """Apply all Alembic migrations on startup."""
    config = Config()
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.attributes["database_url"] = sync_url(database_url)
    command.upgrade(config, "head")


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
