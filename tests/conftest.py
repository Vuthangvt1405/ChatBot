from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import OpenRouterSettings, Settings
from app.db import SessionDep
from app.main import create_app
from app.services import get_chat_service
from tests.echo import EchoChatService


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Playwright's sync API keeps an event loop running on the main thread once it starts,
    # which breaks any async test after it. Run the browser tests last.
    items.sort(key=lambda item: "e2e" in item.path.parts)


def make_settings(db_path: Path, **overrides) -> Settings:
    """Throwaway SQLite file. Ignores any local .env.

    The app requires a key at startup; tests swap the real provider out, so it's never sent.
    """
    values = {
        "database_url": f"sqlite+aiosqlite:///{db_path.as_posix()}",
        "openrouter": OpenRouterSettings(api_key="test-key"),
        **overrides,
    }
    return Settings(_env_file=None, **values)


def use_echo_provider(app: FastAPI) -> None:
    def echo(session: SessionDep) -> EchoChatService:
        return EchoChatService(session)

    app.dependency_overrides[get_chat_service] = echo


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    app = create_app(make_settings(tmp_path / "chatbot-tests.db"))
    use_echo_provider(app)
    return app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
