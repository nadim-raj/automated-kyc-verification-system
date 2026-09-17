"""Name and text normalisation.

Name comparison fails in boring, predictable ways: accents, honorifics,
transliteration variants, particles, and inconsistent ordering. Normalising
these away before any fuzzy comparison removes most of the noise that would
otherwise land a legitimate customer in a manual queue.
"""

from __future__ import annotations

import re
import unicodedata

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")

#: Titles that carry no identity information.
HONORIFICS = frozenset({"mr", "mrs", "ms", "miss", "dr", "prof", "eng", "hon", "sri"})

#: Particles that appear inconsistently between a document and a form.
PARTICLES = frozenset({"bin", "binti", "bte", "van", "von", "de", "del", "da", "al"})

#: Illustrative transliteration groups. A real deployment maintains these per
#: market, because naming conventions differ and getting them wrong is the
#: single most common cause of false mismatches.
EQUIVALENTS: dict[str, str] = {
    "md": "mohammad",
    "mohd": "mohammad",
    "mohammed": "mohammad",
    "muhammad": "mohammad",
    "mohamad": "mohammad",
    "ahmad": "ahmed",
    "hossain": "hussain",
    "hosain": "hussain",
    "hussein": "hussain",
    "abdul": "abdul",
    "abd": "abdul",
}


def strip_accents(text: str) -> str:
    """Drop combining marks so ``José`` and ``Jose`` compare equal."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    if not text:
        return ""
    folded = strip_accents(text).casefold()
    folded = _PUNCT.sub(" ", folded)
    return _WHITESPACE.sub(" ", folded).strip()


def name_tokens(
    name: str,
    *,
    drop_honorifics: bool = True,
    drop_particles: bool = True,
) -> tuple[str, ...]:
    """Normalise a name into comparable tokens."""
    out: list[str] = []
    for token in normalize(name).split():
        if drop_honorifics and token in HONORIFICS:
            continue
        if drop_particles and token in PARTICLES:
            continue
        out.append(EQUIVALENTS.get(token, token))
    return tuple(t for t in out if t)


def initials(tokens: tuple[str, ...]) -> str:
    return "".join(token[0] for token in tokens if token)


def normalize_document_number(value: str | None) -> str:
    """Normalise a document number for comparison.

    Optical character recognition confuses a small set of glyph pairs. Folding
    them before comparison avoids sending a case to a human because a zero was
    read as the letter O.
    """
    if not value:
        return ""
    confusions = str.maketrans({"O": "0", "Q": "0", "I": "1", "L": "1", "S": "5", "B": "8", "Z": "2"})
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return cleaned.translate(confusions)
