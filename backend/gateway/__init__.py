"""
HTTP Gateway — thin REST/SSE wrapper around the gRPC service.

Render's load balancer terminates TLS and forwards HTTP/1.1 to your container.
While Render lists HTTP/2 support, gRPC over public internet through their proxy
is unreliable. This gateway provides a guaranteed-working HTTP endpoint.

Architecture:
    Browser ←─ SSE ─→ Next.js API Route (Vercel) ←─ HTTP/SSE ─→ This Gateway ←─ in-process ─→ StoryGenerator

Endpoints:
    POST /generate         — SSE stream of generated tokens
    GET  /health           — Health check (Render uses this)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

# --- path setup ---
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import config
from backend.inference import StoryGenerator

logger = logging.getLogger(__name__)

# Module-level generator (loaded once at startup)
_generator: StoryGenerator | None = None


def _get_generator() -> StoryGenerator:
    global _generator
    if _generator is None:
        _generator = StoryGenerator()
        _generator.load()
    return _generator


# ======================================================================
# FastAPI app
# ======================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model artifacts on startup."""
    logger.info("HTTP Gateway starting — loading model artifacts...")
    _get_generator()
    logger.info("HTTP Gateway ready.")
    yield


app = FastAPI(
    title="Urdu Story Generator — HTTP Gateway",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vercel frontend to call this endpoint
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ── Explicit OPTIONS handler so preflight never hits a 400 ──
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str, request: Request):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        },
    )


# ── Request / Response schemas ──


class GenerateRequest(BaseModel):
    prefix: str = Field(..., description="Starting phrase in Urdu")
    max_length: int = Field(
        default=0,
        description="Max tokens to generate (0 = use default)",
    )


# ── Endpoints ──


@app.get("/health")
async def health():
    gen = _get_generator()
    return {
        "status": "healthy" if gen.is_ready else "degraded",
        "model_loaded": gen.model.is_loaded,
        "tokenizer_loaded": gen.tokenizer.is_loaded,
    }


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Stream generated tokens as Server-Sent Events (SSE).

    Each event is a JSON object:
        data: {"token": "...", "full_text": "...", "is_finished": false}

    The stream ends with is_finished=true.
    """
    generator = _get_generator()

    async def event_stream():
        try:
            for token_text, full_text, is_finished in generator.generate(
                req.prefix, req.max_length
            ):
                payload = json.dumps(
                    {
                        "token": token_text,
                        "full_text": full_text,
                        "is_finished": is_finished,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"

                if not is_finished:
                    await asyncio.sleep(config.generation_delay_ms / 1000.0)
        except Exception as exc:
            logger.exception("Error during generation")
            error_payload = json.dumps(
                {"error": str(exc), "is_finished": True},
                ensure_ascii=False,
            )
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable Nginx buffering if present
        },
    )
