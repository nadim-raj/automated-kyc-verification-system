# Contributing

This is a reference implementation, so the rules are about keeping it honest rather than managing a busy project.

## Before anything else

```bash
make test        # standard library only, no install
make eval        # scores routing against reviewer labels
```

Both must pass. `make eval` exits non-zero if a case a reviewer would have stopped was cleared automatically — that failure is a blocking defect, never something to flag past.

## Rules that are not negotiable

**No real data.** Every fixture is invented. A pull request that adds a real name, document number, image or case identifier will be rejected on sight, not amended.

**No calibrated thresholds.** The values in `policy.py` are placeholders for the demo. Real calibration belongs in private configuration; a published threshold on a fraud control is a published instruction for staying just underneath it.

**No detection specifics.** The repository shows architecture, interfaces, evaluation and operations. It does not document how to evade any of it.

**Telemetry carries no identities.** `observability.personal_data_leaks` asserts this against real cases in the test suite. A new field that trips it is a bug in the field, not the test.

## Changes that need more than a review

**Routing changes** — anything touching `policy.py`, the orchestrator's decision logic, or a signal's score — need:

1. A decision record in `docs/decisions/`, following the existing format.
2. The calibration sweep for the affected band, showing what the change does to escalation and missed escalations.
3. The capacity figure, showing what it costs in reviewer headcount.

The point is that a routing change is a staffing decision and a risk decision at once, and a pull request that shows only the code has shown the least interesting part.

**Label changes** — editing `data/synthetic/labels.json` changes the definition of correct. It needs its own commit, its own explanation, and must never be bundled with the change it makes pass.

## Style

Standard library in the core; heavy dependencies stay behind interfaces in the `ml` extra. Docstrings explain why a thing exists, not what the next line does. Tests describe behaviour in their names.
