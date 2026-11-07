from collections.abc import Sequence

from app.models import Conversation, Message
from app.services.agent_profiles import ChatAgent
from app.services.base import ChatServiceBase


class EchoChatService(ChatServiceBase):
    """Test-only provider: echoes the last message, using the real persistence in ChatServiceBase.

    Lets API tests run the full pipeline without calling OpenRouter.
    """

    async def generate_reply(
        self,
        conversation: Conversation,
        history: Sequence[Message],
        agent: ChatAgent | None = None,
    ) -> str:
        prompt = history[-1].content if history else ""
        return f'[echo] You said: "{prompt}"'
