from __future__ import annotations
import re
from rapidfuzz.distance import Levenshtein
from rapidfuzz import fuzz

HOMOGLYPH_MAP = {
    "0": "o",
    "1": "l",
    "3": "e",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
}

def normalize_identifier(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    for k, v in HOMOGLYPH_MAP.items():
        s = s.replace(k, v)
    return s

def confusability(a: str, b: str) -> dict:
    na, nb = normalize_identifier(a), normalize_identifier(b)
    if not na or not nb:
        return {"lev": None, "ratio": None}
    lev = Levenshtein.distance(na, nb)
    ratio = fuzz.ratio(na, nb) / 100.0
    return {"lev": lev, "ratio": ratio}
