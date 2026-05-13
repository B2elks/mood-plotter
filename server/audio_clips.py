"""Pre-konvertera MP3-klipp till PCM 24kHz mono i minnet vid uppstart.

46elks WebSocket Voice (Beta) kraver PCM 24kHz mono 16-bit. ffmpeg pa
servern gor jobbet.
"""
import logging
import struct
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def mp3_to_pcm(mp3_path: Path) -> bytes:
    """Konvertera en MP3 till raw PCM 24kHz mono 16-bit signed little-endian."""
    result = subprocess.run(
        [
            "ffmpeg", "-loglevel", "error",
            "-i", str(mp3_path),
            "-ar", "24000",
            "-ac", "1",
            "-f", "s16le",
            "pipe:1",
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000) -> bytes:
    """Pack raw PCM med WAV-header for Whisper-API:t."""
    n = len(pcm_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + n, b"WAVE",
        b"fmt ", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
        b"data", n,
    )
    return header + pcm_data


def load_clips(audio_dir: Path, prefix: str) -> list[bytes]:
    """Ladda alla MP3-filer som matchar prefix_* och konvertera till PCM."""
    clips: list[bytes] = []
    for mp3_path in sorted(audio_dir.glob(f"{prefix}_*.mp3")):
        try:
            pcm = mp3_to_pcm(mp3_path)
            clips.append(pcm)
            log.info("Laddade %s (%d B PCM)", mp3_path.name, len(pcm))
        except Exception as e:
            log.error("Kunde inte konvertera %s: %s", mp3_path, e)
    return clips


def rms(pcm_chunk: bytes) -> int:
    """Berakna RMS for en chunk PCM 16-bit signed little-endian."""
    if not pcm_chunk:
        return 0
    n = len(pcm_chunk) // 2
    samples = struct.unpack(f"<{n}h", pcm_chunk[: n * 2])
    if not samples:
        return 0
    s = sum(x * x for x in samples) / n
    return int(s ** 0.5)
