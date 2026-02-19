"""
Unified entrypoint — runs both the gRPC server and HTTP gateway concurrently.

The gRPC server handles direct gRPC clients (grpcurl, local dev, etc.).
The HTTP gateway handles Render's load balancer and the Vercel frontend.

Usage:
    python -m backend.entrypoint          # runs both
    python -m backend.server.main         # gRPC only
    python -m backend.gateway             # HTTP gateway only (via uvicorn)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# ── Resolve model paths relative to the backend/ directory ──────────────────
# This ensures the server works regardless of which directory it is launched
# from (project root, backend/, Docker, etc.).
_BACKEND_DIR = Path(__file__).resolve().parent

def _resolve_path(env_var: str, default: str) -> None:
    """If env_var is set to a relative path, make it absolute from backend/."""
    raw = os.environ.get(env_var, default)
    p = Path(raw)
    if not p.is_absolute():
        os.environ[env_var] = str(_BACKEND_DIR / p)

_resolve_path("TOKENIZER_PATH",    "models/bpe_tokenizer.json")
_resolve_path("TRIGRAM_MODEL_PATH","models/trigram_model.json")
_resolve_path("TRIGRAM_DB_PATH",   "models/trigram_model.db")
_resolve_path("MODEL_DIR",         "models")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    logger = logging.getLogger("entrypoint")

    # Import here so path setup and dotenv loading are done first
    import uvicorn

    from backend.server.main import serve as grpc_serve

    http_port = int(os.getenv("HTTP_PORT", os.getenv("PORT", "10000")))

    logger.info("Starting Urdu Story Generator backend...")
    logger.info("  gRPC  → 0.0.0.0:%s", os.getenv("GRPC_PORT", "50051"))
    logger.info("  HTTP  → 0.0.0.0:%s", http_port)

    # Create both server tasks
    grpc_task = asyncio.create_task(grpc_serve())

    # Uvicorn config for the HTTP gateway
    uvicorn_config = uvicorn.Config(
        "backend.gateway:app",
        host="0.0.0.0",
        port=http_port,
        log_level="info",
        access_log=True,
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    http_task = asyncio.create_task(uvicorn_server.serve())

    # Run both concurrently — if either dies, we shut down
    done, pending = await asyncio.wait(
        [grpc_task, http_task],
        return_when=asyncio.FIRST_EXCEPTION,
    )

    for task in done:
        if task.exception():
            logger.error("Server crashed: %s", task.exception())

    for task in pending:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
