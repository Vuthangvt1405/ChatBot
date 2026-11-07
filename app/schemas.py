import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

from app.models import AgentTool, ThinkingLevel

# Longest allowed message, shared by the API and the chat page (US-3 BR-2).
MAX_MESSAGE_LENGTH = 4000

# STORY-01 Agent Studio limits, shared by the API and the Studio form (via the options endpoint).
MAX_AGENT_NAME_LENGTH = 60
MAX_SYSTEM_PROMPT_LENGTH = 3000
MAX_MODEL_ID_LENGTH = 200
MAX_AGENTS_PER_WORKSPACE = 50
# AC5: the exact text for a blank name or blank instructions.
AGENT_REQUIRED_MESSAGE = "Agent name and system instructions are required."
NAME_CONTROL_CHARACTERS_MESSAGE = "The name must not contain line breaks or control characters."
DUPLICATE_TOOLS_MESSAGE = "Each tool can only be listed once."
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Lengths are measured after trimming, like chat messages (US-3 BR-1).
AgentName = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=MAX_AGENT_NAME_LENGTH)
]
AgentPrompt = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=MAX_SYSTEM_PROMPT_LENGTH)
]


class CamelModel(BaseModel):
    """JSON uses camelCase (conversationId, createdAt), same as the original API."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )


class ChatRequest(CamelModel):
    """Request body for POST /api/chat."""

    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Existing conversation to continue. Omit to start a new conversation.",
    )
    agent_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "STORY-01 AC14: the saved agent that answers this message. Must belong to the "
            "caller's workspace, else 404 and nothing is saved. Omit for the default assistant."
        ),
    )
    message: str = Field(
        min_length=1, max_length=MAX_MESSAGE_LENGTH, description="The user's message."
    )

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The message must not be blank.")
        return value


class ChatResponse(CamelModel):
    """Result of a chat turn: the assistant's reply plus the ids needed to continue."""

    conversation_id: uuid.UUID
    message_id: uuid.UUID
    reply: str
    created_at: datetime


class MessageOut(CamelModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationOut(CamelModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    messages: list[MessageOut]


# ---------- STORY-01 Agent Studio ----------
# Plan: docs/features/plans/ai-data-studio/STORY-01-agent-studio-plan.md §4.3


class AgentProfileRequest(CamelModel):
    """Body of POST /api/agents (create) and PUT /api/agents/{agentId} (edit) (plan D7).

    Server-owned fields (id, workspaceId, timestamps) are not declared, so they are ignored
    if sent (SEC4).
    """

    name: AgentName = Field(
        description=(
            "What the engineer calls this co-pilot; shown in the header. 1-60 characters after "
            "trimming, no control characters, unique in the workspace ignoring case."
        ),
    )
    system_prompt: AgentPrompt = Field(
        description=(
            "Instructions sent as the system message on every chat turn. "
            "1-3000 characters after trimming."
        ),
    )
    model_id: str = Field(
        max_length=MAX_MODEL_ID_LENGTH,
        description="The LLM that does the agent's reasoning (AC4). Must be a supported model.",
    )
    enabled_tools: list[AgentTool] = Field(
        max_length=len(AgentTool),
        description=(
            "Tools the agent may use (AC2). No duplicates; stored in canonical order. "
            "A new agent starts with none (plan D17)."
        ),
    )
    thinking_level: ThinkingLevel = Field(
        default=ThinkingLevel.MEDIUM,
        description="How hard the agent thinks before answering (AC13). Defaults to MEDIUM.",
    )

    @model_validator(mode="before")
    @classmethod
    def _missing_is_blank(cls, data: object) -> object:
        # AC5: a missing name or instructions gets the same message as a blank one, under the
        # same JSON key (name / systemPrompt).
        if isinstance(data, dict):
            for alias, field in (("name", "name"), ("systemPrompt", "system_prompt")):
                if alias not in data and field not in data:
                    data = {**data, alias: ""}
        return data

    @field_validator("name", "system_prompt")
    @classmethod
    def _required(cls, value: str) -> str:
        # AC5: the value is already trimmed, so blank means empty. A custom error keeps the
        # exact text (no "Value error, " prefix).
        if not value:
            raise PydanticCustomError("required", AGENT_REQUIRED_MESSAGE)
        return value

    @field_validator("name")
    @classmethod
    def _no_control_characters(cls, value: str) -> str:
        # AC1, SEC6: line breaks or hidden characters would break the header.
        if _CONTROL_CHARACTERS.search(value):
            raise PydanticCustomError("control_characters", NAME_CONTROL_CHARACTERS_MESSAGE)
        return value

    @field_validator("enabled_tools")
    @classmethod
    def _unique_canonical_tools(cls, value: list[AgentTool]) -> list[AgentTool]:
        # AC2: one toolset looks the same however it was clicked.
        if len(set(value)) != len(value):
            raise PydanticCustomError("duplicate_tools", DUPLICATE_TOOLS_MESSAGE)
        order = list(AgentTool)
        return sorted(value, key=order.index)


class AgentProfileOut(CamelModel):
    """A saved agent as returned by GET/POST/PUT. workspaceId and nameKey are left out (SEC5)."""

    id: uuid.UUID = Field(description="Used for edits and sent with each chat message (AC14).")
    name: str
    system_prompt: str
    model_id: str
    enabled_tools: list[AgentTool]
    thinking_level: ThinkingLevel
    created_at: datetime
    updated_at: datetime = Field(description="Last saved; shown in the Saved agents picker.")


class ModelOptionOut(CamelModel):
    id: str = Field(description="OpenRouter model id; the only values accepted as modelId.")
    label: str


class ToolOptionOut(CamelModel):
    id: AgentTool
    label: str = Field(description="Switch label, e.g. 'Web Search & Crawl' (AC2).")
    description: str


class ThinkingLevelOptionOut(CamelModel):
    id: ThinkingLevel
    label: str
    description: str


class PresetOut(CamelModel):
    id: str = Field(description="Stable text id, e.g. 'red-team-adversary'.")
    title: str
    system_prompt: str = Field(description="Text that Load Preset puts in the instructions (AC3).")


class AgentStudioLimitsOut(CamelModel):
    name_max_length: int
    system_prompt_max_length: int
    max_agents: int


class AgentStudioOptionsOut(CamelModel):
    """Everything the Studio form needs when it opens (GET /api/agent-studio/options)."""

    models: list[ModelOptionOut] = Field(description="Model dropdown choices (AC4).")
    default_model_id: str = Field(
        description="Preselected for a new agent; used by chat with no agent selected (AC11)."
    )
    tools: list[ToolOptionOut] = Field(description="The four switches (AC2).")
    thinking_levels: list[ThinkingLevelOptionOut] = Field(description="Dropdown choices (AC13).")
    default_thinking_level: ThinkingLevel
    presets: list[PresetOut] = Field(description="Load Preset choices (AC3).")
    limits: AgentStudioLimitsOut
