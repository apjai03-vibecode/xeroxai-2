import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "XeroxAI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Ollama / Gemma Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "gemma2:2b")
    OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "8.0"))
    
    # Sentry Settings
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    TRACES_SAMPLE_RATE: float = float(os.getenv("TRACES_SAMPLE_RATE", "1.0"))
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.onrender.com",
        "*"
    ]

settings = Settings()
