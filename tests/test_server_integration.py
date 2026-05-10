"""Integrationstest för aiohttp-servern."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import server


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr("config.AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr("config.COOLDOWN_DB", tmp_path / "cd.db")
    monkeypatch.setattr("config.PI_TOKEN", "test-token")
    monkeypatch.setattr("config.DRY_RUN", True)
    (tmp_path / "audio").mkdir()
    (tmp_path / "audio" / "q_01.mp3").write_bytes(b"x")

    app = server.create_app()
    async with TestClient(TestServer(app)) as c:
        yield c


@pytest.mark.asyncio
async def test_trigger_requires_auth(client):
    resp = await client.post("/trigger", json={"pi_id": "desk1"})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_trigger_calls_46elks_when_authorized(client):
    with patch("server.elks_handler.initiate_call", new=AsyncMock(return_value="call-1")):
        resp = await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_trigger_returns_429_on_cooldown(client):
    with patch("server.elks_handler.initiate_call", new=AsyncMock(return_value="call-1")):
        await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
        resp = await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status == 429


@pytest.mark.asyncio
async def test_elks_answer_returns_play_record_action(client):
    resp = await client.get("/elks/answer?callid=abc")
    body = await resp.json()
    assert "play" in body
    assert "next" in body
    assert "record" in body["next"]


@pytest.mark.asyncio
async def test_audio_serves_existing_file(client, tmp_path):
    (tmp_path / "audio" / "q_test.mp3").write_bytes(b"hello")
    resp = await client.get("/audio/q_test.mp3")
    assert resp.status == 200
    assert await resp.read() == b"hello"


@pytest.mark.asyncio
async def test_audio_404_for_missing_file(client):
    resp = await client.get("/audio/nope.mp3")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_audio_blocks_path_traversal(client):
    resp = await client.get("/audio/../config.py")
    assert resp.status in (400, 404)
