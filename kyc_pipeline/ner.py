"""Pulling person names out of free-text fields.

Registration forms collect names in one box, and people put all sorts of things
in it. A named-entity model finds the person name inside the noise; a heuristic
keeps the pipeline running when the model is not installed.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

_CAPITALISED_RUN = re.compile(r"\b([A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+)*)\b")


@runtime_checkable
class NameExtractor(Protocol):
    def extract(self, text: str) -> list[str]: ...


class HeuristicNameExtractor:
    """Runs of capitalised words, longest first. No dependencies."""

    def extract(self, text: str) -> list[str]:
        if not text:
            return []
        found = [m.group(1).strip() for m in _CAPITALISED_RUN.finditer(text)]
        return sorted(found, key=len, reverse=True)


class SpacyNameExtractor:
    """spaCy ``PERSON`` entities. Requires the ``ml`` extra and a downloaded model."""

    def __init__(self, model: str = "en_core_web_sm") -> None:
        import spacy  # imported lazily so the base install stays dependency-free

        self._nlp = spacy.load(model)

    def extract(self, text: str) -> list[str]:
        if not text:
            return []
        doc = self._nlp(text)
        return [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]


def default_extractor(*, prefer_spacy: bool = True, model: str = "en_core_web_sm") -> NameExtractor:
    """Return spaCy when it is importable and the model is present, else the heuristic."""
    if prefer_spacy:
        try:
            return SpacyNameExtractor(model)
        except Exception:  # noqa: BLE001 - any failure falls back by design
            pass
    return HeuristicNameExtractor()
