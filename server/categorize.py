"""Snabb keyword-baserad emotion-kategorisering av transkriberat svar.

Returnerar en av: happy, tired, stressed, sad, neutral.
"""
import unicodedata


CATEGORIES = ("happy", "tired", "stressed", "sad", "neutral")

KEYWORDS = {
    "happy": [
        "glad", "bra", "super", "harlig", "fantastisk", "underbart",
        "toppen", "kanon", "lycklig", "perfekt", "festligt", "trevligt",
    ],
    "tired": [
        "trott", "utmattad", "sliten", "matt", "orkelos", "kraftlos",
        "somnig", "groggy",
    ],
    "stressed": [
        "stressad", "jobbig", "jaktig", "brattom", "mycket att gora",
        "overbelastad", "frustrerad", "hektisk", "pressad",
    ],
    "sad": [
        "ledsen", "deppig", "dalig", "trakig", "nere", "sorgsen",
        "tung", "nedstamd", "olycklig", "fortvivlad",
    ],
}


def _normalize(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def categorize(text: str) -> str:
    """Klassificera fritext till en kategori. Tom/garbled -> neutral."""
    if not text or not text.strip():
        return "neutral"
    norm = _normalize(text)
    for cat in ("sad", "stressed", "tired", "happy"):
        for kw in KEYWORDS[cat]:
            if kw in norm:
                return cat
    return "neutral"
