import logging
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)

# US-6 AC-11: detail for any error that isn't a known one. The real error is only in the log.
UNEXPECTED_DETAIL = "Something went wrong. Please try again."

_PROBLEM_TYPES = {
    400: "https://tools.ietf.org/html/rfc9110#section-15.5.1",
    404: "https://tools.ietf.org/html/rfc9110#section-15.5.5",
    500: "https://tools.ietf.org/html/rfc9110#section-15.6.1",
    502: "https://tools.ietf.org/html/rfc9110#section-15.6.3",
}


class ConversationNotFoundError(Exception):
    """A request targets a conversation that does not exist."""

    def __init__(self, conversation_id: uuid.UUID) -> None:
        super().__init__(f"Conversation '{conversation_id}' was not found.")
        self.conversation_id = conversation_id


class ChatProviderError(Exception):
    """The upstream chat provider failed. The message is safe to return to clients."""


def problem(status: int, title: str, detail: str | None = None, **extra) -> JSONResponse:
    body = {"type": _PROBLEM_TYPES.get(status, "about:blank"), "title": title, "status": status}
    if detail is not None:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def _is_api(request: Request) -> bool:
    path = request.url.path
    return path == "/api" or path.startswith("/api/")


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # 400 (not FastAPI's default 422) to match the original API.
        # Input values are left out on purpose: they can contain the user's message.
        errors: dict[str, list[str]] = {}
        for error in exc.errors():
            loc = [str(part) for part in error["loc"]]
            key = ".".join(loc[1:]) or loc[0]
            errors.setdefault(key, []).append(error["msg"])
        return problem(400, "One or more validation errors occurred.", errors=errors)

    @app.exception_handler(ConversationNotFoundError)
    async def _not_found(request: Request, exc: ConversationNotFoundError) -> JSONResponse:
        # The message only holds the id the client sent.
        return problem(404, "Conversation not found", str(exc))

    @app.exception_handler(ChatProviderError)
    async def _provider(request: Request, exc: ChatProviderError) -> JSONResponse:
        # Provider messages are fixed, client-safe strings.
        logger.warning("Chat provider failed: %s", exc)
        return problem(502, "Chat provider error", str(exc))

    @app.middleware("http")
    async def _unexpected(request: Request, call_next: RequestResponseEndpoint) -> Response:
        """US-6 AC-11, SEC2: any other /api error becomes a fixed 500 ProblemDetails.

        Only /api is covered; the chat page's /ui routes handle their own errors (SEC8).
        Sits outside FastAPI's debug page, so no stack trace leaks even with debug on.
        """
        if not _is_api(request):
            return await call_next(request)
        try:
            return await call_next(request)
        except Exception:
            # The exception never reaches the body, so its details can't leak.
            logger.exception("Unhandled error on %s %s.", request.method, request.url.path)
            return problem(500, "Unexpected error", UNEXPECTED_DETAIL)
