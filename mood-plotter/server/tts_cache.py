"""Välj slumpmässigt en pre-genererad fråge-MP3."""
import random
from pathlib import Path


def pick_question_url(audio_dir: Path, public_base_url: str) -> str:
    """Returnera en publik URL till en slumpmässig q_*.mp3-fil."""
    candidates = sorted(Path(audio_dir).glob("q_*.mp3"))
    if not candidates:
        raise FileNotFoundError(
            f"Inga q_*.mp3 i {audio_dir} — kör generate_questions.py först"
        )
    chosen = random.choice(candidates)
    return f"{public_base_url.rstrip('/')}/audio/{chosen.name}"
