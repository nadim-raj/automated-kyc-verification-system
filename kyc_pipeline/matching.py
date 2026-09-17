"""Scored comparisons between what the customer claimed and what the document says.

Each function returns a :class:`~kyc_pipeline.domain.Signal` rather than a bare
number, so the orchestrator can tell "these disagree" apart from "this could not
be checked".
"""

from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher

from .domain import DocumentExtract, IdentityClaim, Signal
from .normalize import initials, name_tokens, normalize, normalize_document_number

try:  # pragma: no cover - exercised only when the optional dependency is present
    from rapidfuzz.fuzz import ratio as _rf_ratio
    from rapidfuzz.fuzz import token_set_ratio as _rf_token_set_ratio

    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover
    _HAS_RAPIDFUZZ = False


def sequence_ratio(left: str, right: str) -> float:
    """Character-level similarity in ``[0, 1]``.

    RapidFuzz when installed, the standard library otherwise, so the pipeline
    runs on a clean machine and gets faster when the extra is installed.
    """
    if not left or not right:
        return 0.0
    if _HAS_RAPIDFUZZ:
        return _rf_ratio(left, right) / 100.0
    return SequenceMatcher(None, left, right).ratio()


def token_set_ratio(left: str, right: str) -> float:
    """Order-insensitive token similarity in ``[0, 1]``."""
    if not left or not right:
        return 0.0
    if _HAS_RAPIDFUZZ:
        return _rf_token_set_ratio(left, right) / 100.0
    left_sorted = " ".join(sorted(normalize(left).split()))
    right_sorted = " ".join(sorted(normalize(right).split()))
    return SequenceMatcher(None, left_sorted, right_sorted).ratio()


def score_names(claimed: str, documented: str) -> tuple[float, str]:
    """Compare two names, returning a score and a human-readable explanation."""
    left = name_tokens(claimed)
    right = name_tokens(documented)
    if not left or not right:
        return 0.0, "one of the names is empty after normalisation"
    if left == right:
        return 1.0, "exact match after normalisation"
    if sorted(left) == sorted(right):
        return 0.97, "same tokens in a different order"

    left_set, right_set = set(left), set(right)
    if left_set <= right_set or right_set <= left_set:
        return 0.93, "one name omits tokens the other has, such as a middle name"

    if initials(left) == initials(right) and len(left) == len(right):
        per_token = [sequence_ratio(a, b) for a, b in zip(left, right)]
        return 0.5 + 0.45 * (sum(per_token) / len(per_token)), "matching initials with spelling differences"

    joined_left, joined_right = " ".join(left), " ".join(right)
    score = max(sequence_ratio(joined_left, joined_right), token_set_ratio(joined_left, joined_right))
    return score, "fuzzy similarity"


def name_signal(claim: IdentityClaim, document: DocumentExtract) -> Signal:
    if not claim.full_name or not document.full_name:
        return Signal.missing("name_match", "a name was not supplied on one side")
    score, detail = score_names(claim.full_name, document.full_name)
    return Signal(name="name_match", score=round(score, 4), available=True, detail=detail)


def date_of_birth_signal(claim: IdentityClaim, document: DocumentExtract) -> Signal:
    claimed, documented = claim.date_of_birth, document.date_of_birth
    if claimed is None or documented is None:
        return Signal.missing("dob_match", "a date of birth was not supplied on one side")
    if claimed == documented:
        return Signal(name="dob_match", score=1.0, available=True, detail="dates agree")
    if _transposed(claimed, documented):
        return Signal(
            name="dob_match",
            score=0.5,
            available=True,
            detail="day and month appear transposed, a common data-entry error",
        )
    return Signal(name="dob_match", score=0.0, available=True, detail="dates disagree")


def _transposed(left: date, right: date) -> bool:
    return left.year == right.year and left.day == right.month and left.month == right.day


def document_number_signal(claim: IdentityClaim, document: DocumentExtract) -> Signal:
    claimed = normalize_document_number(claim.document_number)
    documented = normalize_document_number(document.document_number)
    if not claimed or not documented:
        return Signal.missing("document_number_match", "a document number was not supplied on one side")
    if claimed == documented:
        return Signal(
            name="document_number_match",
            score=1.0,
            available=True,
            detail="numbers agree once confusable characters are folded",
        )
    return Signal(
        name="document_number_match",
        score=round(sequence_ratio(claimed, documented), 4),
        available=True,
        detail="numbers differ",
    )


def nationality_signal(claim: IdentityClaim, document: DocumentExtract) -> Signal:
    claimed, documented = normalize(claim.nationality or ""), normalize(document.nationality or "")
    if not claimed or not documented:
        return Signal.missing("nationality_match", "a nationality was not supplied on one side")
    score = 1.0 if claimed == documented else round(sequence_ratio(claimed, documented), 4)
    return Signal(
        name="nationality_match",
        score=score,
        available=True,
        detail="values agree" if score == 1.0 else "values differ",
    )


def text_signals(claim: IdentityClaim, document: DocumentExtract) -> tuple[Signal, ...]:
    """Every comparison that needs no media."""
    return (
        name_signal(claim, document),
        date_of_birth_signal(claim, document),
        document_number_signal(claim, document),
        nationality_signal(claim, document),
    )
