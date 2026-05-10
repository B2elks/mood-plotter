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


class _FakeResp:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def read(self):
        return b"fake-wav"


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def get(self, url):
        return _FakeResp()


@pytest.mark.asyncio
async def test_elks_recording_returns_personalized_ack_url(client, monkeypatch):
    """Regression: recording response must point at ack_<call_id>.mp3, not fallback."""
    from voice_butler import ButlerResult

    monkeypatch.setattr(
        "voice_butler.transcribe_audio",
        lambda path, api_key: "trött",
    )
    monkeypatch.setattr(
        "voice_butler.analyze_response",
        lambda text, api_key: ButlerResult(
            image_prompt="a peaceful watercolor",
            butler_ack="Förträffligt min herre",
        ),
    )
    monkeypatch.setattr(
        "tts_live.generate_ack_mp3",
        lambda text, call_id, audio_dir, public_base_url, voice_id, api_key: (
            f"{public_base_url}/audio/ack_{call_id}.mp3"
        ),
    )
    monkeypatch.setattr(
        "image_pipeline.generate_svg",
        lambda prompt, api_key: "<svg/>",
    )
    # Avoid real HTTP fetch of the recording URL.
    monkeypatch.setattr("aiohttp.ClientSession", lambda: _FakeSession())

    resp = await client.post(
        "/elks/recording?call_id=abc",
        data={"recordurl": "https://example.com/r.wav"},
    )
    body = await resp.json()
    assert "ack_abc.mp3" in body["play"], (
        f"Expected personalized ack URL but got {body['play']}"
    )
