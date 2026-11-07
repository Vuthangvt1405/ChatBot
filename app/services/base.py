import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConversationNotFoundError
from app.models import Conversation, Message, MessageRole
from app.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 60

# Messages are ordered by time; SQLite's rowid breaks ties when two share a timestamp.
_MESSAGE_ORDER = (Message.created_at, literal_column("messages.rowid"))


class ChatService(Protocol):
    async def send_message(self, request: ChatRequest) -> ChatResponse: ...

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationOut | None: ...


def build_title(message: str) -> str:
    title = message.strip()
    if len(title) <= MAX_TITLE_LENGTH:
        return title
    return title[:MAX_TITLE_LENGTH].rstrip() + "…"


class ChatServiceBase(ABC):
    """Shared conversation persistence. Providers only implement generate_reply."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        db = self.session

        # US-6 AC-7: a turn is saved only once the reply has arrived, so a failed send
        # stores nothing (no half turn, no empty conversation). Nothing is added to the
        # session before then.
        existing: Conversation | None = None
        if request.conversation_id is not None:
            existing = await db.get(Conversation, request.conversation_id)
            if existing is None:
                raise ConversationNotFoundError(request.conversation_id)

        conversation = existing or Conversation(title=build_title(request.message))

        history: list[Message] = []
        if existing is not None:
            history = list(
                await db.scalars(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(*_MESSAGE_ORDER)
                )
            )

        user = Message(
            conversation_id=conversation.id, role=MessageRole.USER, content=request.message
        )
        history.append(user)

        reply = await self.generate_reply(conversation, history)

        # Created after the reply, so it always sorts after the user's message.
        assistant = Message(
            conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=reply
        )

        if existing is None:
            db.add(conversation)
        db.add_all([user, assistant])
        try:
            await db.commit()
        except Exception:
            # SEC4: don't let a failed save's rows ride along with a later one.
            await db.rollback()
            raise

        # Ids and counts only: never log message content.
        logger.info(
            "Conversation %s handled a turn (%d messages).", conversation.id, len(history) + 1
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant.id,
            reply=assistant.content,
            created_at=assistant.created_at,
        )

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationOut | None:
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            return None

        messages = await self.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(*_MESSAGE_ORDER)
        )

        return ConversationOut(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            messages=[MessageOut.model_validate(m) for m in messages],
        )

    @abstractmethod
    async def generate_reply(self, conversation: Conversation, history: Sequence[Message]) -> str:
        """Return the assistant's reply for the conversation so far."""
