"""What a routing threshold costs in reviewer time.

A threshold is usually discussed as a number between zero and one. The people
who live with it experience it as a queue: how many cases arrive for a human
each day, how long each takes, and whether the team finishes them before
tomorrow's arrive.

This module converts between the two. It takes the volume and review time of a
deployment and reports what a given escalation rate means in reviewer-hours,
headcount, and whether the backlog grows or drains. Joined to the calibration
sweep, it prices each band directly: not "escalation rises four points" but
"this setting costs another half a reviewer".

Every input belongs to the deployment. Nothing here is calibrated, and the
defaults exist only so the module runs.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Sequence

from .calibration import BandSweep, sweep_band
from .evaluation import load_cases, load_labels


@dataclass(frozen=True)
class ReviewCapacity:
    """The operating conditions a queue actually runs under."""

    daily_cases: int = 5_000
    minutes_per_review: float = 6.0
    reviewer_hours_per_day: float = 6.0
    reviewers: int = 8

    def __post_init__(self) -> None:
        if self.daily_cases < 0 or self.minutes_per_review <= 0:
            raise ValueError("daily_cases must be non-negative and minutes_per_review positive")
        if self.reviewer_hours_per_day <= 0 or self.reviewers < 0:
            raise ValueError("reviewer_hours_per_day must be positive and reviewers non-negative")

    @property
    def hours_available(self) -> float:
        """Productive review hours per day across the team.

        Deliberately not contracted hours: reviewers also handle escalations,
        training, and everything else a working day contains.
        """
        return self.reviewers * self.reviewer_hours_per_day


@dataclass(frozen=True)
class Workload:
    """What one escalation rate demands of the team."""

    escalation_rate: float
    escalations_per_day: float
    hours_required: float
    reviewers_required: float
    hours_available: float

    @property
    def surplus_hours(self) -> float:
        return self.hours_available - self.hours_required

    @property
    def sustainable(self) -> bool:
        """True when a day's arrivals can be cleared within the same day."""
        return self.hours_required <= self.hours_available

    @property
    def backlog_growth_per_day(self) -> float:
        """Cases added to the queue each day when capacity falls short."""
        if self.sustainable or self.escalations_per_day == 0:
            return 0.0
        shortfall = self.hours_required - self.hours_available
        return shortfall / (self.hours_required / self.escalations_per_day)

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "escalation_rate": round(self.escalation_rate, 4),
            "escalations_per_day": round(self.escalations_per_day, 1),
            "hours_required": round(self.hours_required, 1),
            "hours_available": round(self.hours_available, 1),
            "reviewers_required": round(self.reviewers_required, 2),
            "sustainable": self.sustainable,
            "backlog_growth_per_day": round(self.backlog_growth_per_day, 1),
        }


def workload(capacity: ReviewCapacity, escalation_rate: float) -> Workload:
    """Translate an escalation rate into a day's work."""
    if not 0.0 <= escalation_rate <= 1.0:
        raise ValueError("escalation_rate must be between 0 and 1")
    escalations = capacity.daily_cases * escalation_rate
    hours = escalations * capacity.minutes_per_review / 60.0
    return Workload(
        escalation_rate=escalation_rate,
        escalations_per_day=escalations,
        hours_required=hours,
        reviewers_required=hours / capacity.reviewer_hours_per_day,
        hours_available=capacity.hours_available,
    )


def sustainable_escalation_rate(capacity: ReviewCapacity) -> float:
    """The highest escalation rate the current team clears in a day.

    The number to bring to a staffing conversation: above it the queue grows
    every day, and no amount of effort inside the team changes that.
    """
    if capacity.daily_cases == 0:
        return 1.0
    clearable = capacity.hours_available * 60.0 / capacity.minutes_per_review
    return min(1.0, clearable / capacity.daily_cases)


def reviewers_for(capacity: ReviewCapacity, escalation_rate: float) -> int:
    """Whole reviewers needed to hold a given escalation rate.

    Rounded up, because half a reviewer does not turn up.
    """
    return math.ceil(workload(capacity, escalation_rate).reviewers_required)


def price_sweep(sweep: BandSweep, capacity: ReviewCapacity, total_cases: int) -> list[dict[str, float | bool | str]]:
    """Attach a staffing cost to every point of a calibration sweep.

    This is the join that matters. Calibration says a band change moves the
    escalation rate; capacity says what that movement costs in people.
    """
    priced = []
    for point in sweep.points:
        rate = point.escalated / total_cases if total_cases else 0.0
        load = workload(capacity, rate)
        priced.append(
            {
                "band": sweep.band,
                "value": point.value,
                "escalation_rate": round(rate, 4),
                "reviewers_required": round(load.reviewers_required, 2),
                "whole_reviewers": math.ceil(load.reviewers_required),
                "missed_escalations": point.missed_escalations,
                "sustainable": load.sustainable,
            }
        )
    return priced


def format_report(capacity: ReviewCapacity, priced: Sequence[dict], band: str) -> str:
    lines: list[str] = []
    ceiling = sustainable_escalation_rate(capacity)
    lines.append("Operating conditions")
    lines.append(
        f"  {capacity.daily_cases:,} cases a day · {capacity.minutes_per_review:g} min per review · "
        f"{capacity.reviewers} reviewers × {capacity.reviewer_hours_per_day:g}h = "
        f"{capacity.hours_available:g} review hours a day"
    )
    lines.append("")
    lines.append(f"Highest escalation rate this team clears in a day: {ceiling:.0%}")
    lines.append("  Above it the queue grows every day, whatever the team does.")
    lines.append("")
    lines.append(f"What each setting of {band} costs")
    lines.append("   value   escalation   reviewers   whole   sustainable   missed")
    for row in priced:
        flag = "  <-- misses an escalation" if row["missed_escalations"] else ""
        lines.append(
            f"   {row['value']:<7.2f} {row['escalation_rate']:^11.0%} "
            f"{row['reviewers_required']:^11.2f} {row['whole_reviewers']:^7} "
            f"{'yes' if row['sustainable'] else 'NO':^13} {row['missed_escalations']:^6}{flag}"
        )
    lines.append("")
    lines.append("Reviewer counts are a floor: they assume every hour is spent reviewing,")
    lines.append("no absence, no ramp-up, and no case taking longer than average.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-cases", type=int, default=5_000)
    parser.add_argument("--minutes-per-review", type=float, default=6.0)
    parser.add_argument("--reviewer-hours", type=float, default=6.0)
    parser.add_argument("--reviewers", type=int, default=8)
    parser.add_argument("--band", default="name_auto_clear")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    capacity = ReviewCapacity(
        daily_cases=args.daily_cases,
        minutes_per_review=args.minutes_per_review,
        reviewer_hours_per_day=args.reviewer_hours,
        reviewers=args.reviewers,
    )
    cases = load_cases(None)
    labels = load_labels(None)
    sweep = sweep_band(args.band, cases, labels)
    priced = price_sweep(sweep, capacity, len(cases))

    if args.json:
        print(json.dumps({
            "capacity": {
                "daily_cases": capacity.daily_cases,
                "minutes_per_review": capacity.minutes_per_review,
                "hours_available": capacity.hours_available,
                "sustainable_escalation_rate": round(sustainable_escalation_rate(capacity), 4),
            },
            "priced_band": priced,
        }, indent=2))
    else:
        print(format_report(capacity, priced, args.band))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
