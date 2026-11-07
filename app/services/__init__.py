from typing import Annotated

from fastapi import Depends, Request

from app.db import SessionDep
from app.services.base import ChatService
from app.services.openrouter import OpenRouterChatService


def get_chat_service(request: Request, session: SessionDep) -> ChatService:
    """The OpenRouter provider. Tests swap it out via app.dependency_overrides."""
    return OpenRouterChatService(
        session, request.app.state.http_client, request.app.state.settings.openrouter
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
