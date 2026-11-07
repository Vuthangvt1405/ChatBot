import logging
from collections.abc import Sequence

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import OpenRouterSettings
from app.errors import ChatProviderError
from app.models import Conversation, Message, MessageRole
from app.services.base import ChatServiceBase

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60

# US-6 AC-8: fixed, client-safe messages for provider outages (shown as 502 by the API).
UNREACHABLE_MESSAGE = "The chat provider could not be reached."
TIMEOUT_MESSAGE = "The chat provider did not respond in time."
UNREADABLE_MESSAGE = "The chat provider returned an unreadable response."
REJECTED_MESSAGE = (
    "The chat provider rejected the request. Check the API key, model name, and quota."
)
EMPTY_MESSAGE = "The chat provider returned an empty response."


def create_http_client(settings: OpenRouterSettings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.base_url.rstrip("/") + "/",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


class OpenRouterChatService(ChatServiceBase):
    """Sends the conversation to OpenRouter's /chat/completions endpoint and returns the reply."""

    def __init__(
        self, session: AsyncSession, http: httpx.AsyncClient, settings: OpenRouterSettings
    ) -> None:
        super().__init__(session)
        self._http = http
        self._settings = settings

    async def generate_reply(self, conversation: Conversation, history: Sequence[Message]) -> str:
        options = self._settings
        messages: list[dict[str, str]] = []

        if options.system_prompt.strip():
            messages.append({"role": MessageRole.SYSTEM, "content": options.system_prompt})

        max_history = max(1, options.max_history_messages)
        messages.extend({"role": m.role, "content": m.content} for m in history[-max_history:])

        headers = {"Authorization": f"Bearer {options.api_key}"}
        if options.site_url and options.site_url.strip():
            headers["HTTP-Referer"] = options.site_url
        if options.app_name and options.app_name.strip():
            headers["X-Title"] = options.app_name

        response = await self._post(
            "chat/completions",
            json={"model": options.model, "messages": messages},
            headers=headers,
        )

        if not response.is_success:
            logger.error(
                "OpenRouter request failed with %d: %s",
                response.status_code,
                response.text[:1000],
            )
            raise ChatProviderError(REJECTED_MESSAGE)

        try:
            payload = response.json()
        except ValueError:
            # US-6 AC-8: garbage from the provider is an outage, not a crash.
            logger.exception("OpenRouter sent an unreadable response for model %s.", options.model)
            raise ChatProviderError(UNREADABLE_MESSAGE) from None

        content = _first_content(payload)
        if not content or not content.strip():
            logger.error("OpenRouter returned an empty completion for model %s.", options.model)
            raise ChatProviderError(EMPTY_MESSAGE)

        return content

    async def _post(self, url: str, **kwargs) -> httpx.Response:
        """US-6 AC-8: a timeout or an unreachable provider becomes a ChatProviderError (502).

        A cancelled request (asyncio.CancelledError) is not an outage, so it still propagates.
        """
        try:
            return await self._http.post(url, **kwargs)
        except httpx.TimeoutException:
            logger.exception("OpenRouter did not respond in time.")
            raise ChatProviderError(TIMEOUT_MESSAGE) from None
        except httpx.RequestError:
            logger.exception("OpenRouter could not be reached.")
            raise ChatProviderError(UNREACHABLE_MESSAGE) from None


def _first_content(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None
