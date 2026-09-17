"""Run the pipeline over the synthetic cases and print what it decided."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .orchestrator import Orchestrator
from .providers import load_case
from .synthetic import generate

DEFAULT_FIXTURES = Path("data/synthetic/cases.json")


def load_payloads(path: Path | None) -> list[dict[str, Any]]:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return generate()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--limit", type=int, default=0, help="only evaluate the first N cases")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args(argv)

    payloads = load_payloads(args.fixtures)
    if args.limit:
        payloads = payloads[: args.limit]

    orchestrator = Orchestrator()
    rows = []
    for payload in payloads:
        case = load_case(payload)
        decision = orchestrator.evaluate(case)
        rows.append((case, decision))

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "case_id": case.case_id,
                        "provider": case.provider.value,
                        "outcome": decision.outcome.value,
                        "reasons": list(decision.reasons),
                        "scores": {s.name: s.score for s in decision.signals if s.available},
                    }
                    for case, decision in rows
                ],
                indent=2,
            )
        )
        return 0

    width = max((len(case.case_id) for case, _ in rows), default=10) + 2
    print(f"{'case':<{width}}{'provider':<16}{'outcome':<12}why")
    print("-" * (width + 28 + 50))
    for case, decision in rows:
        why = decision.reasons[0] if decision.reasons else "all checks within the auto-clear band"
        if len(why) > 66:
            why = why[:63] + "..."
        print(f"{case.case_id:<{width}}{case.provider.value:<16}{decision.outcome.value:<12}{why}")

    cleared = sum(1 for _, d in rows if d.outcome.value == "auto_clear")
    print()
    print(f"{cleared} of {len(rows)} cases cleared without a reviewer; {len(rows) - cleared} escalated.")
    print("Automatic declines are disabled by design: the pipeline clears or escalates, people decline.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
