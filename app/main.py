import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import MissingApiKeyError, Settings
from app.db import make_engine, run_migrations
from app.errors import add_exception_handlers
from app.routers import agents, api, health, pages
from app.services.openrouter import create_http_client

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Checked on startup (not import), so the server stops with a clear error.
        if not settings.openrouter.api_key.strip():
            raise MissingApiKeyError()

        await asyncio.to_thread(run_migrations, settings.database_url)
        app.state.http_client = create_http_client(settings.openrouter)
        try:
            yield
        finally:
            await app.state.http_client.aclose()
            await engine.dispose()

    app = FastAPI(
        title="Chatbot API",
        version="v1",
        description="A small chat API with persisted conversations, backed by OpenRouter.",
        docs_url="/swagger",
        redoc_url=None,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    add_exception_handlers(app)
    app.include_router(api.router)
    app.include_router(agents.router)
    app.include_router(health.router)
    app.include_router(pages.router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
