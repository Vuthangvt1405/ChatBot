"""The chat page and the HTML fragments HTMX swaps into it."""

import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.errors import ChatProviderError, ConversationNotFoundError
from app.schemas import MAX_MESSAGE_LENGTH, ChatRequest
from app.services import ChatServiceDep

logger = logging.getLogger(__name__)

# Jinja autoescaping is on, so replies are always rendered as text, never as HTML.
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"max_length": MAX_MESSAGE_LENGTH})


@router.post("/ui/send", response_class=HTMLResponse)
async def send(
    request: Request,
    chat: ChatServiceDep,
    message: Annotated[str, Form()] = "",
    conversation_id: Annotated[str, Form()] = "",
) -> Response:
    """Returns the assistant's message as an <li>; the conversation id is in a header.

    US-6: a failure is only a status code with an empty body (404 conversation gone,
    502 provider unavailable, 500 anything else). The page picks the fixed text to show,
    so exception details never reach the visitor (BR-1).
    """
    try:
        chat_request = ChatRequest(message=message, conversation_id=conversation_id or None)
    except ValidationError:
        return Response(status_code=400)

    try:
        reply = await chat.send_message(chat_request)
    except Exception as exc:
        status = (
            404
            if isinstance(exc, ConversationNotFoundError)
            else 502
            if isinstance(exc, ChatProviderError)
            else 500
        )
        # Never log the message text (US-4 SEC3).
        logger.exception(
            "Chat send failed (%d) for conversation %s", status, chat_request.conversation_id
        )
        return Response(status_code=status)

    response = templates.TemplateResponse(
        request, "_message.html", {"role": "assistant", "text": reply.reply}
    )
    response.headers["X-Conversation-Id"] = str(reply.conversation_id)
    return response


@router.get("/ui/conversations/{conversation_id}", response_class=HTMLResponse)
async def history(request: Request, conversation_id: uuid.UUID, chat: ChatServiceDep) -> Response:
    """US-5: the saved conversation's messages as <li> items, or 404 if it no longer exists."""
    try:
        conversation = await chat.get_conversation(conversation_id)
    except Exception:
        # Log the id only, never content (US-5 SEC4).
        logger.exception("Restoring conversation %s failed", conversation_id)
        return Response(status_code=500)

    if conversation is None:
        return Response(status_code=404)

    return templates.TemplateResponse(
        request, "_messages.html", {"messages": conversation.messages}
    )
