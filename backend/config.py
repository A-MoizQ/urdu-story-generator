"""
Configuration management for the backend service.
All settings are loaded from environment variables with sensible defaults.

APP_ENV controls the runtime mode:
    - "development" → uses mock story data (no model artifacts needed)
    - "production"  → requires real tokenizer + trigram model files
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Central configuration for the story generation backend."""

    # --- Environment ---
    app_env: str = field(
        default_factory=lambda: os.getenv("APP_ENV", "development")
    )

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

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

    # --- Generation defaults ---
    default_max_length: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_MAX_LENGTH", "200"))
    )
    generation_delay_ms: int = field(
        default_factory=lambda: int(os.getenv("GENERATION_DELAY_MS", "50"))
    )

    # --- Special tokens (unused Unicode bytes as per assignment) ---
    # These should match whatever your teammate picks during preprocessing.
    eos_token: str = field(
        default_factory=lambda: os.getenv("EOS_TOKEN", "\uFDD0")
    )  # Sentence boundary
    eop_token: str = field(
        default_factory=lambda: os.getenv("EOP_TOKEN", "\uFDD1")
    )  # Paragraph boundary
    eot_token: str = field(
        default_factory=lambda: os.getenv("EOT_TOKEN", "\uFDD2")
    )  # Story boundary

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
