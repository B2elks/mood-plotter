#!/usr/bin/env python3
"""Ring & Vinn — Live game show server.

Runs:
- 46elks WebSocket server (ELKS_WS_PORT) for phone calls
- Show WebSocket server (SHOW_WS_PORT) for the TV frontend
- HTTP server (HTTP_PORT) for voice_start webhook
- Show engine that orchestrates the game
"""

import asyncio
import base64
import glob as glob_module
import json
import logging
import os
import random
import sys
from collections import deque
from datetime import datetime, timezone

import websockets
from dotenv import load_dotenv

from audio import play_audio, transcribe_audio, wait_for_speech_then_silence, CODEC
from judge import judge_answer

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELKS_USER = os.getenv("ELKS_USER")
ELKS_PASS = os.getenv("ELKS_PASS")

if not OPENAI_API_KEY or not ELKS_USER or not ELKS_PASS:
    log.error("Missing env vars: OPENAI_API_KEY, ELKS_USER, ELKS_PASS")
    sys.exit(1)

SHOW_WS_PORT = int(os.getenv("SHOW_WS_PORT", "8115"))
ELKS_WS_PORT = int(os.getenv("ELKS_WS_PORT", "8116"))
HTTP_PORT = int(os.getenv("HTTP_PORT", "8117"))
ELKS_WS_NUMBER = os.getenv("ELKS_WS_NUMBER", "+4600700021")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
LEADERBOARD_FILE = os.path.join(BASE_DIR, "leaderboard.json")

# --- Clip loading ---

clips = {}
question_clips = {}


def load_clips():
    for prefix in ("intro", "welcome", "qintro", "correct", "wrong",
                   "queue", "ending", "next", "nocallers"):
        clips[prefix] = []
        for f in sorted(glob_module.glob(os.path.join(CLIPS_DIR, f"{prefix}_*.pcm"))):
            with open(f, "rb") as fh:
                clips[prefix].append(fh.read())
        log.info("Loaded %d %s clips", len(clips[prefix]), prefix)

    for f in sorted(glob_module.glob(os.path.join(CLIPS_DIR, "questions", "q_*.pcm"))):
        qid = int(os.path.basename(f).split("_")[1].split(".")[0])
        with open(f, "rb") as fh:
            question_clips[qid] = fh.read()
    log.info("Loaded %d question clips", len(question_clips))


def random_clip(category):
    c = clips.get(category, [])
    return random.choice(c) if c else None


# --- State ---

show_clients = set()
call_queue = deque()
leaderboard = {}
questions = []
current_question_idx = 0
show_running = False


def load_questions():
    global questions
    with open(QUESTIONS_FILE) as f:
        questions = json.load(f)
    log.info("Loaded %d questions", len(questions))


def save_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)


# --- Show WebSocket (frontend) ---

async def broadcast(event):
    msg = json.dumps(event)
    for ws in list(show_clients):
        try:
            await ws.send(msg)
        except Exception:
            show_clients.discard(ws)


async def handle_show_client(ws):
    show_clients.add(ws)
    log.info("Show client connected (%d total)", len(show_clients))
    try:
        await ws.send(json.dumps({
            "type": "init",
            "leaderboard": leaderboard,
            "queue_size": len(call_queue),
            "question_idx": current_question_idx,
            "total_questions": len(questions),
            "running": show_running,
        }))
        async for msg in ws:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        show_clients.discard(ws)
        log.info("Show client disconnected (%d total)", len(show_clients))


# --- 46elks call handling ---

async def handle_elks_call(ws):
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(raw)
    except Exception:
        return

    msg_type = data.get("t") or data.get("type")
    if msg_type not in ("hello", "call_started"):
        return

    call_id = data.get("callid") or data.get("call_id", "unknown")
    caller_from = data.get("from", "anonymous")
    log.info("Call from %s (id=%s)", caller_from, call_id)

    await ws.send(json.dumps({"t": "sending", "format": CODEC}))
    await ws.send(json.dumps({"t": "listening", "format": CODEC}))

    caller_audio = bytearray()
    call_closed = asyncio.Event()

    async def record():
        try:
            async for message in ws:
                msg = json.loads(message)
                mt = msg.get("t") or msg.get("type")
                if mt == "audio":
                    caller_audio.extend(base64.b64decode(msg["data"]))
                elif mt in ("bye", "close", "hangup"):
                    break
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            call_closed.set()

    record_task = asyncio.create_task(record())

    queue_clip = random_clip("queue")
    if queue_clip and not call_closed.is_set():
        await play_audio(ws, queue_clip)

    ready_event = asyncio.Event()
    entry = {
        "call_id": call_id,
        "caller_from": caller_from,
        "ws": ws,
        "caller_audio": caller_audio,
        "call_closed": call_closed,
        "record_task": record_task,
        "ready_event": ready_event,
    }
    call_queue.append(entry)
    await broadcast({"type": "queue_update", "size": len(call_queue)})
    log.info("Caller %s added to queue (size=%d)", caller_from, len(call_queue))

    done, pending = await asyncio.wait(
        [asyncio.create_task(ready_event.wait()),
         asyncio.create_task(call_closed.wait())],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
        t.cancel()

    if call_closed.is_set() and not ready_event.is_set():
        if entry in call_queue:
            call_queue.remove(entry)
            await broadcast({"type": "queue_update", "size": len(call_queue)})
        log.info("Caller %s hung up from queue", caller_from)
        return

    await call_closed.wait()

    if not record_task.done():
        try:
            await asyncio.wait_for(record_task, timeout=3)
        except asyncio.TimeoutError:
            record_task.cancel()


# --- Show Engine ---

async def run_show():
    global current_question_idx, show_running
    show_running = True

    load_questions()
    leaderboard.clear()

    await broadcast({"type": "show_state", "state": "intro"})
    await asyncio.sleep(3)

    for idx, question in enumerate(questions):
        current_question_idx = idx

        await broadcast({
            "type": "question",
            "idx": idx,
            "total": len(questions),
            "question": question["question"],
            "q_type": question.get("type", "quiz"),
            "points": question.get("points", 1),
        })
        await broadcast({"type": "show_state", "state": "asking"})
        log.info("Question %d: %s", idx + 1, question["question"])

        waited = 0
        while not call_queue and waited < 30:
            await asyncio.sleep(1)
            waited += 1
            if waited % 10 == 0:
                await broadcast({"type": "show_state", "state": "waiting"})

        if not call_queue:
            log.info("No callers for question %d, skipping", idx + 1)
            await broadcast({"type": "show_state", "state": "waiting"})
            await asyncio.sleep(2)
            continue

        entry = call_queue.popleft()
        await broadcast({"type": "queue_update", "size": len(call_queue)})

        caller_ws = entry["ws"]
        caller_audio = entry["caller_audio"]
        call_closed = entry["call_closed"]
        caller_from = entry["caller_from"]
        caller_name = caller_from[-4:] if len(caller_from) > 4 else caller_from

        await broadcast({
            "type": "caller_active",
            "name": caller_name,
            "caller_from": caller_from,
        })
        await broadcast({"type": "show_state", "state": "listening"})
        log.info("Picked caller %s for question %d", caller_name, idx + 1)

        entry["ready_event"].set()

        if call_closed.is_set():
            log.info("Caller already gone")
            continue

        welcome_clip = random_clip("welcome")
        if welcome_clip and not call_closed.is_set():
            await play_audio(caller_ws, welcome_clip)

        q_clip = question_clips.get(question["id"])
        if q_clip and not call_closed.is_set():
            await play_audio(caller_ws, q_clip)

        if not call_closed.is_set():
            speech_start = len(caller_audio)
            spoke = await wait_for_speech_then_silence(
                caller_audio, call_closed, start_pos=speech_start, timeout_checks=60
            )

            if spoke:
                speech_data = bytes(caller_audio[speech_start:])
                transcript = await transcribe_audio(speech_data)
                log.info("Transcript: %s", transcript)

                await broadcast({
                    "type": "answer",
                    "name": caller_name,
                    "transcript": transcript,
                })

                result = judge_answer(question, transcript)
                log.info("Result: %s", result)

                if result["correct"]:
                    pts = question.get("points", 1)
                    leaderboard[caller_name] = leaderboard.get(caller_name, 0) + pts
                    save_leaderboard()
                    correct_clip = random_clip("correct")
                    if correct_clip and not call_closed.is_set():
                        await play_audio(caller_ws, correct_clip)
                    await broadcast({"type": "show_state", "state": "correct"})
                else:
                    wrong_clip = random_clip("wrong")
                    if wrong_clip and not call_closed.is_set():
                        await play_audio(caller_ws, wrong_clip)
                    await broadcast({"type": "show_state", "state": "wrong"})

                await broadcast({
                    "type": "result",
                    "name": caller_name,
                    "correct": result["correct"],
                    "explanation": result.get("explanation", ""),
                    "points": question.get("points", 1) if result["correct"] else 0,
                })
                await broadcast({"type": "leaderboard", "scores": leaderboard})
            else:
                log.info("No speech detected from caller")
                await broadcast({"type": "show_state", "state": "wrong"})

        if not call_closed.is_set():
            try:
                await caller_ws.send(json.dumps({"t": "hangup"}))
            except Exception:
                pass

        await asyncio.sleep(3)

        if idx < len(questions) - 1:
            await broadcast({"type": "show_state", "state": "idle"})
            await broadcast({"type": "leaderboard", "scores": leaderboard})
            await asyncio.sleep(2)

    await broadcast({"type": "show_state", "state": "ended"})
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_lb[0] if sorted_lb else None
    await broadcast({
        "type": "show_ended",
        "winner": {"name": winner[0], "points": winner[1]} if winner else None,
        "leaderboard": leaderboard,
    })
    log.info("Show ended! Winner: %s", winner)
    show_running = False


# --- HTTP server ---

async def handle_http(reader, writer):
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=5)
        if not request_line:
            return

        parts = request_line.decode().strip().split()
        method = parts[0] if parts else "GET"
        path = (parts[1] if len(parts) > 1 else "/").split("?")[0]

        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break

        body = json.dumps({"connect": ELKS_WS_NUMBER}).encode()
        if path == "/voice/start":
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"\r\n"
            ).encode()
        elif path == "/api/start":
            if not show_running:
                asyncio.create_task(run_show())
                resp = json.dumps({"ok": True, "message": "Show started"}).encode()
            else:
                resp = json.dumps({"ok": False, "message": "Show already running"}).encode()
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(resp)}\r\n"
                f"\r\n"
            ).encode()
            body = resp
        elif path == "/api/status":
            status = json.dumps({
                "running": show_running,
                "queue_size": len(call_queue),
                "question_idx": current_question_idx,
                "total_questions": len(questions),
                "leaderboard": leaderboard,
            }).encode()
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(status)}\r\n"
                f"\r\n"
            ).encode()
            body = status
        else:
            msg = b'{"error":"not found"}'
            header = (
                f"HTTP/1.1 404 Not Found\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(msg)}\r\n"
                f"\r\n"
            ).encode()
            body = msg

        writer.write(header + body)
        await writer.drain()
    except Exception as e:
        log.error("HTTP error: %s", e)
    finally:
        writer.close()


# --- Main ---

async def main():
    load_clips()
    load_questions()

    await asyncio.start_server(handle_http, "0.0.0.0", HTTP_PORT)
    log.info("HTTP server on port %d", HTTP_PORT)

    async with websockets.serve(handle_show_client, "0.0.0.0", SHOW_WS_PORT):
        log.info("Show WS on port %d", SHOW_WS_PORT)
        async with websockets.serve(handle_elks_call, "0.0.0.0", ELKS_WS_PORT):
            log.info("46elks WS on port %d", ELKS_WS_PORT)
            log.info("Ring & Vinn ready! POST /api/start to begin")
            await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
