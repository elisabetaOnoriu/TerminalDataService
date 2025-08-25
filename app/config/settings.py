from __future__ import annotations
from functools import lru_cache
from typing import Optional, Literal
from pydantic import Field, AnyUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables (.env)."""

    # Allow .env and ignore extra variables
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App env ---
    ENV: Literal["local", "dev", "staging", "prod"] = "local"

    # --- AWS / LocalStack configuration ---
    AWS_ACCESS_KEY_ID: str = Field(default="test")
    AWS_SECRET_ACCESS_KEY: str = Field(default="test")
    AWS_REGION: str = Field(default="eu-central-1")

    # LocalStack base endpoint (containers: http://localstack:4566, host: http://localhost:4566)
    LOCALSTACK_ENDPOINT: Optional[AnyUrl] = Field(default="http://localhost:4566")

    # Optional explicit SQS endpoint (overrides LOCALSTACK_ENDPOINT if provided)
    SQS_ENDPOINT_URL: Optional[AnyUrl] = None

    # Optional: explicit full queue URL (if set, use this and skip construction)
    TERMINAL_SQS_QUEUE_URL: Optional[AnyUrl] = None

    # Fallback pieces to build a LocalStack queue URL when TERMINAL_SQS_QUEUE_URL is not set
    ACCOUNT_ID: str = Field(default="000000000000")
    QUEUE_NAME: str = Field(default="device-messages")

    # --- Simulation knobs (optional, used by simulators/tests) ---
    NUM_DEVICES: int = Field(default=3, ge=1)
    SEND_INTERVAL_SEC: int = Field(default=2, ge=1, le=5)

    # Optional database DSN (some services may use it)
    DATABASE_URL: Optional[str] = None

    # ---- Derived helpers ----
    @property
    def sqs_effective_endpoint(self) -> Optional[str]:
        """Return the effective SQS endpoint (SQS_ENDPOINT_URL > LOCALSTACK_ENDPOINT > None)."""
        return str(self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT) if (self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT) else None

    @property
    def queue_url(self) -> Optional[str]:
        """Return explicit queue URL if provided, otherwise construct LocalStack-style URL."""
        if self.TERMINAL_SQS_QUEUE_URL:
            return str(self.TERMINAL_SQS_QUEUE_URL)
        if self.sqs_effective_endpoint:
            # LocalStack queue URL format: {endpoint}/{account_id}/{queue_name}
            base = self.sqs_effective_endpoint.rstrip("/")
            return f"{base}/{self.ACCOUNT_ID}/{self.QUEUE_NAME}"
        return None

    def ensure_valid(self) -> None:
        """Fail fast on invalid combinations."""
        # In prod, you likely don't want to hit LocalStack by mistake.
        if self.ENV == "prod" and (self.LOCALSTACK_ENDPOINT or self.SQS_ENDPOINT_URL):
            raise ValueError("LocalStack endpoints must not be configured in production.")
        # Basic sanity for queue identification
        if not (self.TERMINAL_SQS_QUEUE_URL or self.QUEUE_NAME):
            raise ValueError("Either TERMINAL_SQS_QUEUE_URL or QUEUE_NAME must be set.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        s = Settings()
        s.ensure_valid()
        return s
    except (ValidationError, ValueError) as e:
        # Crash fast at startup if required envs are missing/invalid
        raise RuntimeError(f"[settings] Invalid configuration: {e}") from e
