import asyncio

import pytest

from ws_dispatcher import WSDispatcher


class FakeWS:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send_json(self, obj):
        self.sent.append(obj)

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_register_adds_ready_client():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    assert d.get_ready_client() is ws


@pytest.mark.asyncio
async def test_unregister_removes_client():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    d.unregister(ws)
    assert d.get_ready_client() is None


@pytest.mark.asyncio
async def test_send_svg_marks_client_busy():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")

    sent = await d.send_svg("<svg/>")

    assert sent is True
    assert ws.sent == [{"method": "plot", "svg": "<svg/>"}]
    assert d.get_ready_client() is None


@pytest.mark.asyncio
async def test_mark_ready_returns_to_ready_pool():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    await d.send_svg("<svg/>")

    d.mark_ready(ws)
    assert d.get_ready_client() is ws


@pytest.mark.asyncio
async def test_send_svg_returns_false_when_no_ready():
    d = WSDispatcher()
    sent = await d.send_svg("<svg/>")
    assert sent is False
