"""Helpers for keeping personal data out of logs and metrics.

Reviewers need the real values; dashboards, logs and error trackers do not. The
split matters: verification systems handle exactly the data you least want
sprayed across a log aggregator.
"""

from __future__ import annotations

import hashlib


def mask_name(name: str | None) -> str:
    """``Kazi Nadimul Haque`` becomes ``K*** N*** H***``."""
    if not name:
        return ""
    parts = [p for p in name.split() if p]
    return " ".join(f"{p[0]}{'*' * max(len(p) - 1, 0)}" for p in parts)


def mask_number(value: str | None, keep: int = 4) -> str:
    """Keep the last few characters, mask the rest."""
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]


def pseudonymize(value: str | None, salt: str, length: int = 16) -> str:
    """A stable, salted identifier for joining records without storing the value.

    The salt must be secret and rotated like any other key; without one, a hash
    of a national ID number is trivially reversible by brute force.
    """
    if not value:
        return ""
    digest = hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()
    return digest[:length]
