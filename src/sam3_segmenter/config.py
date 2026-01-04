"""Configuration settings for the SAM3 Drawing Segmenter service."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model settings
    model_path: str = "sam3.pt"
    default_confidence_threshold: float = 0.3

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://localhost:8000",
    ]

    # GPU settings (None = auto-detect)
    device: Optional[str] = None

    # Exemplars directory
    exemplars_dir: str = "./exemplars"

    # Batch processing settings
    max_batch_size: int = 10

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_prefix": "SAM3_",
        "extra": "ignore",
    }


settings = Settings()
