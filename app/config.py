from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenRouterSettings(BaseModel):
    # Secret: set OPENROUTER__API_KEY in .env or the environment, never in code.
    # Required: the app refuses to start without it (see create_app).
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1/"
    model: str = "stealth/crouton-alpha"
    system_prompt: str = "You are a helpful, concise assistant."
    # Optional attribution headers forwarded to OpenRouter.
    site_url: str | None = None
    app_name: str | None = None
    # How many recent messages to send as context.
    max_history_messages: int = 20

    @field_validator("base_url", "model")
    @classmethod
    def _required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OpenRouter base_url and model are required.")
        return value


class Settings(BaseSettings):
    """App settings, read from the environment and an optional .env file.

    Nested keys use a double underscore, e.g. OPENROUTER__API_KEY.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///chatbot.db"
    # FastAPI debug mode (tracebacks on unhandled errors). /api/* still answers with a safe
    # ProblemDetails body when it's on (US-6 AC-11, SEC2).
    debug: bool = False
    openrouter: OpenRouterSettings = OpenRouterSettings()


class MissingApiKeyError(RuntimeError):
    """Raised at startup when OPENROUTER__API_KEY is not set."""

    def __init__(self) -> None:
        super().__init__(
            "OPENROUTER__API_KEY is required. Copy .env.example to .env and set it, "
            "or pass it as an environment variable."
        )
