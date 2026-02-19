"""
Configuration management for the backend service.
All settings are loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Central configuration for the story generation backend."""

    # --- Server ---
    grpc_host: str = field(
        default_factory=lambda: os.getenv("GRPC_HOST", "0.0.0.0")
    )
    grpc_port: int = field(
        default_factory=lambda: int(os.getenv("GRPC_PORT", "50051"))
    )
    max_workers: int = field(
        default_factory=lambda: int(os.getenv("MAX_WORKERS", "4"))
    )

    # --- Model artifacts ---
    model_dir: str = field(
        default_factory=lambda: os.getenv("MODEL_DIR", "models")
    )
    tokenizer_path: str = field(
        default_factory=lambda: os.getenv(
            "TOKENIZER_PATH", "models/bpe_tokenizer.json"
        )
    )
    trigram_model_path: str = field(
        default_factory=lambda: os.getenv(
            "TRIGRAM_MODEL_PATH", "models/trigram_model.json"
        )
    )
    trigram_db_path: str = field(
        default_factory=lambda: os.getenv(
            "TRIGRAM_DB_PATH", "models/trigram_model.db"
        )
    )

    # --- Generation defaults ---
    default_max_length: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_MAX_LENGTH", "200"))
    )
    generation_delay_ms: int = field(
        default_factory=lambda: int(os.getenv("GENERATION_DELAY_MS", "50"))
    )

    # --- CORS ---
    cors_origins: str = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*")
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


# Singleton instance
config = Config()
