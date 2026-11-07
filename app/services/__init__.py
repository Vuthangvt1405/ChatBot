from typing import Annotated

from fastapi import Depends, Request

from app.db import SessionDep
from app.services.agent_profiles import AgentProfileService
from app.services.base import ChatService
from app.services.openrouter import OpenRouterChatService
from app.workspace import CurrentWorkspaceDep


def get_chat_service(
    request: Request, session: SessionDep, workspace: CurrentWorkspaceDep
) -> ChatService:
    """The OpenRouter provider. Tests swap it out via app.dependency_overrides.

    STORY-01: gets the workspace and the agent service so a message's agentId can be resolved.
    """
    settings = request.app.state.settings.openrouter
    return OpenRouterChatService(
        session,
        request.app.state.http_client,
        settings,
        agents=AgentProfileService(session, settings),
        workspace_id=workspace,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
