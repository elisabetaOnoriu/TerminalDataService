# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy Poetry files first (better layer caching)
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-root

# Copy application code
COPY . .

EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["python", "-c", "print('Container up')"]
