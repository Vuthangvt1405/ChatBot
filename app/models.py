import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, TypeDecorator, text
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship


class MessageRole:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AgentTool(StrEnum):
    """The four tool switches in Agent Studio (STORY-01 AC2), in their canonical order."""

    WEB_SEARCH = "WEB_SEARCH"
    CORPUS_EDA = "CORPUS_EDA"
    SYNTHESIZER = "SYNTHESIZER"
    RECIPE_BUILDER = "RECIPE_BUILDER"


class ThinkingLevel(StrEnum):
    """How hard the agent's model reasons before answering (STORY-01 AC13)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Stores UTC as a naive SQLite timestamp and hands back timezone-aware values."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return value.replace(tzinfo=UTC) if value is not None else None


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class Conversation(Base):
    """A chat conversation, owning an ordered set of messages."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default_factory=utc_now)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        default_factory=list,
        repr=False,
    )


class Message(Base):
    """A single message in a Conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    # One of the MessageRole values.
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default_factory=utc_now)

    conversation: Mapped[Conversation | None] = relationship(
        back_populates="messages", default=None, repr=False
    )


class AgentProfile(Base):
    """A saved Super-Agent: name, instructions, model, thinking level and tool switches.

    STORY-01. There is no "active" flag: the page remembers the selected agent and sends its
    id with each chat message (plan D5).
    """

    __tablename__ = "agent_profiles"
    __table_args__ = (
        Index("ux_agent_profiles_workspace_name_key", "workspace_id", "name_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4)
    # Owner. Every query filters by it (SEC2). No FK: there is no workspace table yet.
    workspace_id: Mapped[uuid.UUID] = mapped_column()
    name: Mapped[str] = mapped_column(String(60))
    # casefold(trimmed name); makes names unique per workspace ignoring case (AC7).
    name_key: Mapped[str] = mapped_column(String(60))
    system_prompt: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(String(200))
    # AgentTool values, canonical order.
    enabled_tools: Mapped[list[str]] = mapped_column(
        JSON, default_factory=list, server_default=text("'[]'")
    )
    # A ThinkingLevel value.
    thinking_level: Mapped[str] = mapped_column(
        String(16), default=ThinkingLevel.MEDIUM.value, server_default=ThinkingLevel.MEDIUM.value
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default_factory=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default_factory=utc_now)
