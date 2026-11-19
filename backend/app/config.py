"""Application configuration module for XeroxAI 2.0.

Provides centralized environment variable loading, service defaults, and Pydantic
settings validation for local Ollama, Sentry observability, and CORS policies.
"""

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Configuration settings for the XeroxAI 2.0 application.

    Attributes:
        PROJECT_NAME: Name of the application service.
        VERSION: Current release version string.
        API_V1_PREFIX: Common root prefix for REST API endpoints.
        OLLAMA_BASE_URL: HTTP endpoint for local Ollama inference daemon.
        GEMMA_MODEL: Default SLM tag name for document extraction and order parsing.
        OLLAMA_TIMEOUT_SECONDS: Timeout threshold for Ollama requests before heuristic fallback.
        SENTRY_DSN: Data Source Name for Sentry tracing integration.
        ENVIRONMENT: Deployment environment identifier (e.g., development, production).
        TRACES_SAMPLE_RATE: Sampling percentage for performance tracing spans.
        CORS_ORIGINS: List of allowed origins for cross-origin browser requests.
    """

    PROJECT_NAME: str = "XeroxAI"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api"

    # Ollama / Gemma Settings
    OLLAMA_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    GEMMA_MODEL: str = Field(
        default_factory=lambda: os.getenv("GEMMA_MODEL", "gemma2:2b")
    )
    OLLAMA_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "8.0"))
    )

    # Sentry Settings
    SENTRY_DSN: str = Field(default_factory=lambda: os.getenv("SENTRY_DSN", ""))
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    TRACES_SAMPLE_RATE: float = Field(
        default_factory=lambda: float(os.getenv("TRACES_SAMPLE_RATE", "1.0"))
    )

    # Cross-Origin Resource Sharing (CORS)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.onrender.com",
        "*",
    ]


settings = Settings()
