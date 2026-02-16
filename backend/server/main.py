"""
gRPC server for the Urdu Story Generation microservice.

Exposes:
    - GenerateStory (server-streaming): streams tokens for ChatGPT-like UX
    - HealthCheck (unary): reports service readiness
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import grpc
from grpc_reflection.v1alpha import reflection

# --- path setup so imports work both locally and in Docker ---
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import config
from backend.inference import StoryGenerator
from backend.mock import MockStoryGenerator

# generated protobuf / gRPC stubs
from backend.proto import story_pb2, story_pb2_grpc

logger = logging.getLogger(__name__)

# Module-level generator instance (loaded once at startup)
_generator: StoryGenerator | MockStoryGenerator | None = None


def _get_generator() -> StoryGenerator | MockStoryGenerator:
    global _generator
    if _generator is None:
        if config.is_development:
            logger.info("APP_ENV=development → using MockStoryGenerator")
            _generator = MockStoryGenerator()
        else:
            _generator = StoryGenerator()
        _generator.load()
    return _generator


# ======================================================================
# Service implementation
# ======================================================================

class StoryGeneratorServicer(story_pb2_grpc.StoryGeneratorServicer):
    """Implements the StoryGenerator gRPC service."""

    async def GenerateStory(
        self,
        request: story_pb2.GenerateRequest,
        context: grpc.aio.ServicerContext,
    ):
        """Server-streaming RPC: yields tokens one at a time."""
        generator = _get_generator()

        prefix = request.prefix.strip()
        max_length = request.max_length if request.max_length > 0 else 0

        logger.info(
            "GenerateStory called — prefix=%r, max_length=%d",
            prefix[:50],
            max_length,
        )

        try:
            for token_text, full_text, is_finished in generator.generate(
                prefix, max_length
            ):
                yield story_pb2.GenerateResponse(
                    token=token_text,
                    is_finished=is_finished,
                    full_text=full_text,
                )
                # Small delay to simulate streaming cadence (configurable)
                if not is_finished:
                    await asyncio.sleep(config.generation_delay_ms / 1000.0)
        except Exception as exc:
            logger.exception("Error during generation")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                f"Generation failed: {exc}",
            )

    async def HealthCheck(
        self,
        request: story_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext,
    ):
        generator = _get_generator()
        return story_pb2.HealthCheckResponse(
            status="healthy" if generator.is_ready else "degraded",
            model_loaded=str(generator.model.is_loaded),
            tokenizer_loaded=str(generator.tokenizer.is_loaded),
        )


# ======================================================================
# Server bootstrap
# ======================================================================

async def serve() -> None:
    """Start the async gRPC server."""
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )

    story_pb2_grpc.add_StoryGeneratorServicer_to_server(
        StoryGeneratorServicer(), server
    )

    # Enable server reflection (useful for debugging with grpcurl)
    service_names = (
        story_pb2.DESCRIPTOR.services_by_name["StoryGenerator"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    listen_addr = f"{config.grpc_host}:{config.grpc_port}"
    server.add_insecure_port(listen_addr)

    logger.info("Starting gRPC server on %s", listen_addr)
    await server.start()

    # Pre-load model artifacts
    _get_generator()

    logger.info("Server ready — listening on %s", listen_addr)
    await server.wait_for_termination()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    asyncio.run(serve())


if __name__ == "__main__":
    main()
