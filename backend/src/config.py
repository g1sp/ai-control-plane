"""Configuration management for the gateway."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./data/audit.db"

    # Gateway mode: "local" (use Ollama) or "remote" (use Claude)
    gateway_mode: str = "local"

    # Models
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    claude_api_key: str = ""

    # Policy
    models_whitelist: List[str] = [
        "ollama",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    ]
    users_whitelist: List[str] = [
        "demo",
        "alice@company.com",
        "bob@company.com",
        "researcher",
    ]

    # Budget limits
    budget_per_request_usd: float = 0.10
    budget_per_user_per_day_usd: float = 10.0
    rate_limit_req_per_minute: int = 60

    # Request timeouts
    request_timeout_seconds: int = 30

    # Injection detection patterns
    injection_patterns: List[str] = [
        "ignore all instructions",
        "you are now",
        "jailbreak",
        "forget everything",
        "disregard",
        "pretend you are",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
