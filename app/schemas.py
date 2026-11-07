import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

# Longest allowed message, shared by the API and the chat page (US-3 BR-2).
MAX_MESSAGE_LENGTH = 4000


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
