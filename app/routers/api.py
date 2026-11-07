import uuid

from fastapi import APIRouter

from app.errors import ConversationNotFoundError
from app.schemas import ChatRequest, ChatResponse, ConversationOut
from app.services import ChatServiceDep

router = APIRouter(prefix="/api/chat", tags=["Chat"])

_PROBLEM = {"content": {"application/problem+json": {}}}


@router.post(
    "",
    response_model=ChatResponse,
    summary="Sends a message and returns the assistant's reply.",
    description="Omit `conversationId` to start a new conversation.",
    responses={400: _PROBLEM, 404: _PROBLEM, 500: _PROBLEM, 502: _PROBLEM},
)
async def send_message(request: ChatRequest, chat: ChatServiceDep) -> ChatResponse:
    # Errors (404 not found, 502 provider, 500 anything else) are mapped in app/errors.py
    # (US-6 AC-11).
    return await chat.send_message(request)


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationOut,
    summary="Returns the stored message history for a conversation.",
    responses={404: _PROBLEM, 500: _PROBLEM},
)
async def get_messages(conversation_id: uuid.UUID, chat: ChatServiceDep) -> ConversationOut:
    conversation = await chat.get_conversation(conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)
    return conversation
