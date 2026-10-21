from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Literal["gemini", "groq"] = "gemini"
    gemini_api_key: SecretStr | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-3.8-flash"
    groq_api_key: SecretStr | None = Field(default=None, repr=False)
    groq_model: str = "openai/gpt-oss-20b"
    max_input_chars: int = Field(default=2000, ge=1, le=2000)
    max_body_bytes: int = Field(default=16384, ge=512, le=65536)
    rate_limit_per_ip: int = Field(default=5, ge=1)
    rate_limit_global: int = Field(default=5, ge=1)
    rate_window_seconds: int = Field(default=60, ge=1)
    max_concurrent_analyses: int = Field(default=2, ge=1, le=20)
    model_attempt_timeout_seconds: float = Field(default=20, gt=0)
    model_total_timeout_seconds: float = Field(default=45, gt=0)
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @model_validator(mode="after")
    def require_selected_provider_key(self):
        key = self.gemini_api_key if self.llm_provider == "gemini" else self.groq_api_key
        if key is None or not key.get_secret_value().strip():
            variable = "GEMINI_API_KEY" if self.llm_provider == "gemini" else "GROQ_API_KEY"
            raise ValueError(
                f"{variable} must be configured when LLM_PROVIDER={self.llm_provider}."
            )
        return self
