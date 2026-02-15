"""
Tests for the HTTP SSE gateway.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.gateway import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "model_loaded" in data
        assert "tokenizer_loaded" in data


@pytest.mark.asyncio
async def test_generate_endpoint_streams_sse():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/generate",
            json={"prefix": "ایک دفعہ", "max_length": 5},
            headers={"Accept": "text/event-stream"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        # Parse SSE events
        events = []
        for line in resp.text.strip().split("\n"):
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                events.append(payload)

        assert len(events) > 0, "Should receive at least one SSE event"
        assert events[-1]["is_finished"], "Last event should mark finished"


@pytest.mark.asyncio
async def test_generate_empty_prefix():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/generate",
            json={"prefix": "", "max_length": 3},
        )
        assert resp.status_code == 200
