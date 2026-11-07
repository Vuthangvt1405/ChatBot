from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenRouterSettings(BaseModel):
    # Secret: set OPENROUTER__API_KEY in .env or the environment, never in code.
    # Required: the app refuses to start without it (see create_app).
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1/"
    model: str = "stealth/crouton-alpha"
    # STORY-01 AC4: models an agent may use (JSON list in .env, e.g.
    # OPENROUTER__SUPPORTED_MODELS=["stealth/crouton-alpha","openai/gpt-4o-mini"]). The default
    # `model` is always added, so out of the box the dropdown offers just that one.
    supported_models: list[str] = Field(default_factory=list)
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

    @field_validator("supported_models")
    @classmethod
    def _no_blank_models(cls, value: list[str]) -> list[str]:
        # STORY-01 G5❌1: fail at startup rather than show a blank dropdown option.
        if any(not model.strip() for model in value):
            raise ValueError("OpenRouter supported_models must not contain blank entries.")
        return value

    @model_validator(mode="after")
    def _default_model_is_supported(self) -> Self:
        # STORY-01 G5✅5: the default model is always selectable.
        if self.model not in self.supported_models:
            self.supported_models = [self.model, *self.supported_models]
        return self


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
