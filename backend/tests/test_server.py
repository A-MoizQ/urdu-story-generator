"""
Tests for the gRPC StoryGenerator service.

Uses grpcio's aio testing utilities for async server-streaming RPCs.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import grpc
import grpc.aio
import pytest

# Ensure project root is importable
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.proto import story_pb2, story_pb2_grpc
from backend.server.main import StoryGeneratorServicer


@pytest.fixture(scope="module")
def event_loop():
    """Create a module-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def grpc_channel(event_loop):
    """Spin up an in-process async gRPC server and return a channel to it."""
    server = grpc.aio.server()
    story_pb2_grpc.add_StoryGeneratorServicer_to_server(
        StoryGeneratorServicer(), server
    )
    port = server.add_insecure_port("[::]:0")  # random free port
    await server.start()

    channel = grpc.aio.insecure_channel(f"localhost:{port}")
    yield channel

    await channel.close()
    await server.stop(grace=0)


@pytest.fixture
def stub(grpc_channel):
    return story_pb2_grpc.StoryGeneratorStub(grpc_channel)


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check(stub):
    """HealthCheck should return a status."""
    response = await stub.HealthCheck(story_pb2.HealthCheckRequest())
    assert response.status in ("healthy", "degraded")
    assert response.tokenizer_loaded in ("True", "False")
    assert response.model_loaded in ("True", "False")


@pytest.mark.asyncio
async def test_generate_story_streams_tokens(stub):
    """GenerateStory should stream at least one response and finish."""
    request = story_pb2.GenerateRequest(
        prefix="ایک دفعہ",
        max_length=10,
    )

    responses = []
    async for resp in stub.GenerateStory(request):
        responses.append(resp)
        if resp.is_finished:
            break

    assert len(responses) > 0, "Should receive at least one streamed response"
    assert responses[-1].is_finished, "Last response should be marked finished"


@pytest.mark.asyncio
async def test_generate_story_empty_prefix(stub):
    """Should handle an empty prefix without crashing."""
    request = story_pb2.GenerateRequest(prefix="", max_length=5)

    responses = []
    async for resp in stub.GenerateStory(request):
        responses.append(resp)
        if resp.is_finished:
            break

    assert len(responses) > 0
