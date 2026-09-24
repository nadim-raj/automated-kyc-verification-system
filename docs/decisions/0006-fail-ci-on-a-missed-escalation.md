# 0006 — Fail CI on a missed escalation

**Status:** accepted

## Context

The evaluation harness scores routing against reviewer labels and reports two errors separately: cases cleared automatically that a reviewer would have stopped, and cases sent to a human who cleared them anyway.

Reporting them is not the same as enforcing them. A metric that only appears in a report gets read attentively for about two weeks.

## Decision

`python -m kyc_pipeline.evaluation` exits non-zero when any labelled case was cleared automatically that a reviewer would have escalated, and CI runs it on every push. A `--allow-missed-escalations` flag exists for local exploration and is not used in CI.

## Consequences

- **The safety property is enforced, not documented.** A change that starts clearing cases a reviewer would stop turns the build red instead of shipping quietly.
- **The asymmetry is encoded.** Unnecessary escalations do not fail the build; they cost reviewer time, which is a trade-off worth making deliberately. Missed escalations are a control failure and get treated as one.
- **Labels become part of the contract.** If the pipeline is right and the label is wrong, the label has to be changed explicitly in a commit somebody reviews — which is the correct amount of friction for redefining what "correct" means.
- **The gate is only as good as the labelled set.** Eleven synthetic cases prove the mechanism, not the pipeline. On real traffic the same gate runs against a reviewer-labelled sample, and its value scales with how well that sample represents the awkward tail.
