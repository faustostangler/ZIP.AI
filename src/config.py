import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized settings for the Zero Inbox Gmail (ZIP) project.
    Validates environment configurations using Pydantic Settings.
    """

    # Google OAuth2 Credentials
    gmail_client_id: str = Field(..., description="Google OAuth2 Client ID")
    gmail_client_secret: str = Field(..., description="Google OAuth2 Client Secret")
    gmail_project_id: str = Field(..., description="Google Project ID")

    # Path settings
    gmail_token_path: Path = Field(
        default=Path("token.json"),
        description="Path to store/retrieve persistent Gmail API token",
    )
    gmail_credentials_path: Path = Field(
        default=Path("credentials.json"),
        description="Path to credentials.json if using file-based config",
    )

    # Processed Senders settings
    processed_senders_json_path: Path = Field(
        default=Path("processed_senders.json"),
        description="Path to store processed senders list",
    )

    # LLM Settings
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider name (e.g. 'ollama')",
    )
    llm_api_key: str | None = Field(
        default=None,
        description="Optional API key for generic LLM endpoint",
    )
    llm_base_url: str | None = Field(
        default=None,
        description="Optional base URL for generic LLM endpoint",
    )

    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base HTTP URL for Ollama local service API",
    )
    ollama_model: str = Field(
        default="llama3:latest",
        description="The local LLM model name to run categorization with",
    )

    # Observability and environment configuration
    log_level: str = Field(default="INFO", description="Standard logging level")
    env: str = Field(
        default="development", description="Application runtime environment"
    )

    # Load from a local .env file in the workspace
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance for import throughout the codebase
# Using fail-fast: if configurations are missing/invalid, this import will raise ValueError during startup
settings = Settings()  # type: ignore[call-arg]

# Setup logging
logging.basicConfig(
    level=logging.getLevelName(settings.log_level.upper()),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("zip")
