# 0002 — Clear or escalate, never auto-decline

**Status:** accepted

## Context

An automated verification pipeline could reject cases as well as approve them. The temptation is obvious: the clearest mismatches are the easiest to classify.

## Decision

The pipeline produces two outcomes in practice: cleared, or escalated with reasons. Automatic declines are disabled by default (`DecisionPolicy.auto_decline_enabled = False`). The code path exists, so the choice is visible rather than hidden, but switching it on is a deliberate act.

## Consequences

- **Nobody is refused by a threshold.** A wrongly rejected customer usually cannot appeal to anything, and often cannot even find out why. Wrongly clearing is recoverable through later controls; wrongly declining damages a real person immediately.
- **Regulatory alignment.** Several jurisdictions restrict solely automated decisions with significant effects. Declining an identity check is such a decision; clearing one is a much weaker claim.
- **Reviewer capacity must exist.** Everything uncertain lands with a human, so the automation is only as good as the queue behind it. That is the correct place for the constraint to bite.
- **The value comes from the clear cases.** Most verifications are unremarkable. Removing those from the queue is where the time is won.
