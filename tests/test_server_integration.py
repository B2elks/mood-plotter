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
    monkeypatch.setattr("config.CARDS_DIR", tmp_path / "cards")
    monkeypatch.setattr("config.COOLDOWN_DB", tmp_path / "cd.db")
    monkeypatch.setattr("config.PI_TOKEN", "test-token")
    monkeypatch.setattr("config.ADMIN_PASSWORD", "admin-pass")
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
async def test_elks_answer_returns_play_with_next_url(client):
    resp = await client.get("/elks/answer?call_id=abc")
    body = await resp.json()
    assert "play" in body
    assert body["next"].startswith("http")
    assert "after_play" in body["next"]
    assert "call_id=abc" in body["next"]


@pytest.mark.asyncio
async def test_elks_after_play_returns_record_url(client):
    resp = await client.get("/elks/after_play?call_id=abc")
    body = await resp.json()
    assert body["record"].startswith("http")
    assert "recording" in body["record"]
    assert "call_id=abc" in body["record"]


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
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def get(self, url):
        return _FakeResp()


@pytest.mark.asyncio
async def test_elks_play_ack_returns_instant_neutral(client, tmp_path):
    """/elks/play_ack must return an ack_neutral URL instantly, no waiting."""
    # Pre-create a neutral ack file so _pick_random_ack finds it.
    (tmp_path / "audio" / "ack_neutral_01.mp3").write_bytes(b"x")

    client.app["pending_calls"]["abc"] = {"state": "calling"}
    ack_resp = await client.get("/elks/play_ack?call_id=abc")
    body = await ack_resp.json()
    assert "ack_neutral" in body["play"]
    assert "play" in body


# Gallery / admin / cards routes (post-server-only-mode addition)

@pytest.mark.asyncio
async def test_gallery_renders_when_empty(client):
    resp = await client.get("/")
    assert resp.status == 200
    body = await resp.text()
    assert "STÄMNINGS-MASKINEN" in body
    assert "Inga kort har skapats ännu" in body


@pytest.mark.asyncio
async def test_gallery_renders_card(client, tmp_path):
    import card_store
    card_store.save_card(
        cards_dir=tmp_path / "cards",
        call_id="g1",
        png_bytes=b"PNG",
        svg_text="<svg/>",
        transcription="hemligt",
        image_prompt="hemligt",
        butler_ack="hemligt",
    )
    resp = await client.get("/")
    body = await resp.text()
    assert "_g1.png" in body
    # Public gallery must NOT leak transcription/prompt/ack
    assert "hemligt" not in body


@pytest.mark.asyncio
async def test_cards_serves_png(client, tmp_path):
    (tmp_path / "cards").mkdir(exist_ok=True)
    (tmp_path / "cards" / "foo.png").write_bytes(b"PNGDATA")
    resp = await client.get("/cards/foo.png")
    assert resp.status == 200
    assert await resp.read() == b"PNGDATA"


@pytest.mark.asyncio
async def test_cards_404_for_missing(client):
    resp = await client.get("/cards/nope.png")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_cards_blocks_traversal(client):
    resp = await client.get("/cards/../config.py")
    assert resp.status in (400, 404)


@pytest.mark.asyncio
async def test_admin_requires_auth(client):
    resp = await client.get("/admin")
    assert resp.status == 401
    assert "Basic" in resp.headers.get("WWW-Authenticate", "")


@pytest.mark.asyncio
async def test_admin_rejects_wrong_password(client):
    import base64 as _b
    creds = _b.b64encode(b"admin:wrong").decode()
    resp = await client.get("/admin", headers={"Authorization": f"Basic {creds}"})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_admin_renders_with_correct_password(client, tmp_path):
    import card_store
    import base64 as _b
    card_store.save_card(
        cards_dir=tmp_path / "cards",
        call_id="adm1",
        png_bytes=b"x",
        svg_text="<svg/>",
        transcription="trött",
        image_prompt="forest",
        butler_ack="förträffligt",
    )
    creds = _b.b64encode(b"admin:admin-pass").decode()
    resp = await client.get("/admin", headers={"Authorization": f"Basic {creds}"})
    assert resp.status == 200
    body = await resp.text()
    # Admin DOES show transcription
    assert "trött" in body
    assert "forest" in body


@pytest.mark.asyncio
async def test_admin_trigger_starts_call(client):
    import base64 as _b
    creds = _b.b64encode(b"admin:admin-pass").decode()
    resp = await client.post(
        "/admin/trigger",
        headers={"Authorization": f"Basic {creds}"},
    )
    # DRY_RUN is true in fixture
    assert resp.status == 200
    body = await resp.text()
    assert "Samtal startat" in body or "call_id" in body
