"""Agent Studio persistence (STORY-01). Every query is limited to one workspace (SEC2).

Plan: docs/features/plans/ai-data-studio/STORY-01-agent-studio-plan.md
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import OpenRouterSettings
from app.db import SessionDep
from app.errors import (
    AgentLimitReachedError,
    AgentNameTakenError,
    AgentNotFoundError,
    UnsupportedModelError,
)
from app.models import AgentProfile, ThinkingLevel, utc_now
from app.schemas import (
    MAX_AGENT_NAME_LENGTH,
    MAX_AGENTS_PER_WORKSPACE,
    MAX_SYSTEM_PROMPT_LENGTH,
    AgentProfileOut,
    AgentProfileRequest,
    AgentStudioLimitsOut,
    AgentStudioOptionsOut,
    ModelOptionOut,
    PresetOut,
    ThinkingLevelOptionOut,
    ToolOptionOut,
)
from app.services.agent_presets import (
    DEFAULT_THINKING_LEVEL,
    PRESETS,
    THINKING_LABELS,
    TOOL_LABELS,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatAgent:
    """What one chat turn needs from the selected agent (AC4, AC13)."""

    system_prompt: str
    model_id: str
    thinking_level: ThinkingLevel


def name_key(name: str) -> str:
    """AC7: names are unique per workspace ignoring case (also for non-ASCII letters)."""
    return name.casefold()


class AgentProfileService:
    """Saved agents for a workspace. Plays the ticket's AgentProfileRepository role."""

    def __init__(self, session: AsyncSession, settings: OpenRouterSettings) -> None:
        self.session = session
        self._settings = settings

    async def list_agents(self, workspace_id: uuid.UUID) -> list[AgentProfileOut]:
        rows = await self.session.scalars(
            select(AgentProfile)
            .where(AgentProfile.workspace_id == workspace_id)
            .order_by(AgentProfile.name_key)
        )
        return [AgentProfileOut.model_validate(row) for row in rows]

    async def get_agent(self, workspace_id: uuid.UUID, agent_id: uuid.UUID) -> AgentProfileOut:
        return AgentProfileOut.model_validate(await self._load(workspace_id, agent_id))

    async def get_chat_agent(self, workspace_id: uuid.UUID, agent_id: uuid.UUID) -> ChatAgent:
        profile = await self._load(workspace_id, agent_id)
        model_id = profile.model_id
        if model_id not in self._settings.supported_models:
            # A config change must not break chat: fall back, and say which agent (never its
            # instructions).
            logger.warning(
                "Agent %s uses a model that is no longer supported; using the default model.",
                profile.id,
            )
            model_id = self._settings.model
        return ChatAgent(
            system_prompt=profile.system_prompt,
            model_id=model_id,
            thinking_level=ThinkingLevel(profile.thinking_level),
        )

    async def create_agent(
        self, workspace_id: uuid.UUID, request: AgentProfileRequest
    ) -> AgentProfileOut:
        self._check_model(request)

        count = await self.session.scalar(
            select(func.count())
            .select_from(AgentProfile)
            .where(AgentProfile.workspace_id == workspace_id)
        )
        if count >= MAX_AGENTS_PER_WORKSPACE:
            raise AgentLimitReachedError()

        key = name_key(request.name)
        await self._ensure_name_free(workspace_id, key)

        profile = AgentProfile(
            workspace_id=workspace_id,
            name=request.name,
            name_key=key,
            system_prompt=request.system_prompt,
            model_id=request.model_id,
            enabled_tools=[tool.value for tool in request.enabled_tools],
            thinking_level=request.thinking_level.value,
        )
        self.session.add(profile)
        await self._commit()
        self._log_saved(profile)
        return AgentProfileOut.model_validate(profile)

    async def update_agent(
        self, workspace_id: uuid.UUID, agent_id: uuid.UUID, request: AgentProfileRequest
    ) -> AgentProfileOut:
        profile = await self._load(workspace_id, agent_id)
        self._check_model(request)

        key = name_key(request.name)
        await self._ensure_name_free(workspace_id, key, except_id=profile.id)

        # D3: no edit-conflict check; the last save wins.
        profile.name = request.name
        profile.name_key = key
        profile.system_prompt = request.system_prompt
        profile.model_id = request.model_id
        profile.enabled_tools = [tool.value for tool in request.enabled_tools]
        profile.thinking_level = request.thinking_level.value
        profile.updated_at = utc_now()
        await self._commit()
        self._log_saved(profile)
        return AgentProfileOut.model_validate(profile)

    def get_options(self) -> AgentStudioOptionsOut:
        return AgentStudioOptionsOut(
            models=[ModelOptionOut(id=m, label=m) for m in self._settings.supported_models],
            default_model_id=self._settings.model,
            tools=[
                ToolOptionOut(id=tool, label=label, description=description)
                for tool, (label, description) in TOOL_LABELS.items()
            ],
            thinking_levels=[
                ThinkingLevelOptionOut(id=level, label=label, description=description)
                for level, (label, description) in THINKING_LABELS.items()
            ],
            default_thinking_level=DEFAULT_THINKING_LEVEL,
            presets=[
                PresetOut(id=p.id, title=p.title, system_prompt=p.system_prompt) for p in PRESETS
            ],
            limits=AgentStudioLimitsOut(
                name_max_length=MAX_AGENT_NAME_LENGTH,
                system_prompt_max_length=MAX_SYSTEM_PROMPT_LENGTH,
                max_agents=MAX_AGENTS_PER_WORKSPACE,
            ),
        )

    async def _load(self, workspace_id: uuid.UUID, agent_id: uuid.UUID) -> AgentProfile:
        # SEC2: ownership is part of the query, so "not yours" and "doesn't exist" look the same.
        profile = await self.session.scalar(
            select(AgentProfile).where(
                AgentProfile.id == agent_id, AgentProfile.workspace_id == workspace_id
            )
        )
        if profile is None:
            raise AgentNotFoundError()
        return profile

    def _check_model(self, request: AgentProfileRequest) -> None:
        # AC8, SEC6: only allow-listed models, compared exactly.
        if request.model_id not in self._settings.supported_models:
            raise UnsupportedModelError()

    async def _ensure_name_free(
        self, workspace_id: uuid.UUID, key: str, except_id: uuid.UUID | None = None
    ) -> None:
        query = select(AgentProfile.id).where(
            AgentProfile.workspace_id == workspace_id, AgentProfile.name_key == key
        )
        if except_id is not None:
            query = query.where(AgentProfile.id != except_id)
        if await self.session.scalar(query) is not None:
            raise AgentNameTakenError()

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            # SEC9: another save took the name in between; nothing is saved.
            await self.session.rollback()
            raise AgentNameTakenError() from None
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def _log_saved(profile: AgentProfile) -> None:
        # SEC10: ids and counts only, never the instructions.
        logger.info(
            "Agent %s saved in workspace %s (%d tools, thinking %s).",
            profile.id,
            profile.workspace_id,
            len(profile.enabled_tools),
            profile.thinking_level,
        )


def get_agent_profile_service(request: Request, session: SessionDep) -> AgentProfileService:
    return AgentProfileService(session, request.app.state.settings.openrouter)


AgentProfileServiceDep = Annotated[AgentProfileService, Depends(get_agent_profile_service)]
