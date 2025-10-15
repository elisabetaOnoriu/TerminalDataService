# app/config/settings.py
from __future__ import annotations
from pathlib import Path
from typing import Optional
from pydantic import Field, AnyUrl, ValidationError, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables

    This class uses Pydantic's `BaseSettings` for automatic environment
    variable parsing and validation. Required fields must be provided,
    otherwise validation will fail at startup.

    """
    model_config = {"env_file": ".env", "extra": "ignore"}

    AWS_ACCESS_KEY_ID: str = Field(..., description="AWS access key (required)")
    AWS_SECRET_ACCESS_KEY: str = Field(..., description="AWS secret key (required)")
    AWS_REGION: str = Field(..., description="AWS region (required)")

    SQS_QUEUE_URL: AnyUrl = Field(..., description="Full SQS queue URL (required)")
    SQS_ENDPOINT_URL: AnyUrl | None = None

    DB_USER: str = Field(..., description="DB user")
    DB_HOST: str = Field(..., description="DB host")
    DB_PORT: int = Field(..., description="DB port")
    DB_NAME: str = Field(..., description="DB name")
    DB_PASS_FILE: str = Field(..., description="Path to file that contains ONLY the password")
    DATABASE_URL: str | None = None

    SQS_POLL_INTERVAL: float = Field(..., gt=0)
    SQS_WAIT_TIME_SECONDS: int = Field(..., ge=1, le=20)
    SQS_MAX_MESSAGES: int = Field(..., ge=1, le=10)
    SQS_THREAD_POOL_SIZE: int = Field(..., ge=1)
    SQS_VISIBILITY_TIMEOUT: int = Field(..., ge=1)

    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_MAX_MESSAGES: int = Field(..., ge=1, description="Maximum number of messages to keep in Redis")

    @model_validator(mode="after")
    def _post_validate(self) -> "Settings":
        """
        Perform post-initialization validation and derived settings construction.
        - Ensures that if the SQS queue URL points to LocalStack, an explicit
          `SQS_ENDPOINT_URL` must be provided.
        - Builds `DATABASE_URL` dynamically from DB parameters and the password
          file, if it is not already provided.

        """
        if str(self.SQS_QUEUE_URL).startswith(("http://localhost:4566", "https://localhost:4566")) \
           and not self.SQS_ENDPOINT_URL:
            raise ValueError(
                "SQS_QUEUE_URL points to LocalStack but no SQS_ENDPOINT_URL provided. "
                "Set SQS_ENDPOINT_URL=http://localhost:4566"
            )

        if not self.DATABASE_URL:
            pw_path = Path(self.DB_PASS_FILE)
            if not pw_path.exists():
                raise ValueError(f"DB_PASS_FILE not found: {pw_path}")
            password = pw_path.read_text(encoding="utf-8").strip()
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return self

    @property
    def sqs_effective_endpoint(self) -> Optional[str]:
        """
        Return the effective SQS endpoint URL.
        """
        return str(self.SQS_ENDPOINT_URL) if self.SQS_ENDPOINT_URL else None


def get_settings() -> Settings:
    """
    Load and validate application settings.

    This function instantiates the `Settings` object, which loads configuration
    from environment variables or a `.env` file, validates them, and performs
    post-processing.
    """
    try:
        return Settings()
    except (ValidationError, ValueError) as e:
        raise RuntimeError(f"[settings] Invalid configuration: {e}") from e
