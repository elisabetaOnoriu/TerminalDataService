"""
verify .env settings
"""
from __future__ import annotations
from functools import lru_cache
from typing import Optional, Literal
from pydantic import Field, AnyUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables (.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    AWS_ACCESS_KEY_ID: str = Field(default="test")
    AWS_SECRET_ACCESS_KEY: str = Field(default="test")
    AWS_REGION: str = Field(default="eu-central-1")
    LOCALSTACK_ENDPOINT: Optional[AnyUrl] = Field(default="http://localhost:4566")
    SQS_ENDPOINT_URL: Optional[AnyUrl] = None
    TERMINAL_SQS_QUEUE_URL: Optional[AnyUrl] = None
    ACCOUNT_ID: str = Field(default="000000000000")
    QUEUE_NAME: str = Field(default="device-messages")
    NUM_DEVICES: int = Field(default=3, ge=1)
    SEND_INTERVAL_SEC: int = Field(default=2, ge=1, le=5)

    DATABASE_URL: Optional[str] = None

    @property
    def sqs_effective_endpoint(self) -> Optional[str]:
        """Return the effective SQS endpoint (SQS_ENDPOINT_URL > LOCALSTACK_ENDPOINT > None)."""
        return str(self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT) \
            if (self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT) else None

    @property
    def queue_url(self) -> Optional[str]:
        """Return explicit queue URL if provided, otherwise construct LocalStack-style URL."""
        if self.TERMINAL_SQS_QUEUE_URL:
            return str(self.TERMINAL_SQS_QUEUE_URL)
        if self.sqs_effective_endpoint:
            base = self.sqs_effective_endpoint.rstrip("/")
            return f"{base}/{self.ACCOUNT_ID}/{self.QUEUE_NAME}"
        return None

def get_settings() -> Settings:
    """ return settings"""
    try:
        s = Settings()
        s.ensure_valid()
        return s
    except (ValidationError, ValueError) as e:
        raise RuntimeError(f"[settings] Invalid configuration: {e}") from e
