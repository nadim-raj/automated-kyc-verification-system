# Threat model

Who would attack an identity check, what they would try, and what the design does about it.

Written at the level of categories and responses. It names no thresholds, no detection specifics and no evasion techniques, because a threat model for a live control that reads like a checklist of what to avoid is a gift to the people you are modelling.

## Who

**The applicant themselves.** Someone verifying an identity they are not entitled to use — a borrowed document, a coached session, an account opened on behalf of somebody who cannot open one. The most common case by far, and usually opportunistic rather than sophisticated.

**A broker.** Someone doing this at volume on behalf of others, who will probe the boundary deliberately and share what works.

**An insider.** Someone with reviewer access, or with access to the configuration that decides what reaches a reviewer at all.

## What they try, and what answers it

| Attempt | What the design does |
|---|---|
| Documents and details that do not correspond | Field-level comparison, with normalisation so legitimate variation does not hide real mismatch |
| Someone else present, coaching or substituting | Presence and identity-consistency checks across sampled frames, not only at the start |
| A provider that supplies less evidence | Provider capability is modelled explicitly, and clearing on thinner evidence is a policy decision rather than an accident |
| Repeated attempts to find what passes | Not solved here. Rate and repetition belong to a layer that sees across cases, which this one deliberately does not |
| Pressure to loosen a band to drain a queue | The runbook names it as the thing not to do, and the evaluation gate fails the build if routing starts clearing what reviewers would stop |
| A quiet change that weakens a check | Routing changes require a decision record, and CI scores routing against reviewer labels on every push |

## What is deliberately out of scope

- **Document authenticity.** Whether a document is genuine is a different problem, usually answered by the provider.
- **Cross-case patterns.** Repetition, velocity and shared attributes across applicants need a view this pipeline does not have, by design.
- **Sanctions and watchlist screening.** A separate control with separate obligations.
- **Account behaviour after verification.** Verification is a gate, not a monitor.

Saying so matters: a system that implies it covers these creates more risk than one that states its boundaries and lets the next control own them.

## The insider case

The one most systems handle worst. Three choices here bear on it:

- Reviewer access to full case data should be logged and attributable; the packet exists so a reviewer gets what they need and no more.
- Telemetry carries no identities, so the wide-access surface is the one without personal data in it.
- Routing configuration is code, reviewed like code, with a decision record for anything that changes what clears automatically. A threshold quietly edited in a console is the cheapest attack in this entire document.

## Assurance

The pipeline is not asked to be trusted. It is asked to be checkable:

- Every decision carries its reasons, so an unexpected outcome can be explained rather than guessed at.
- Every check that could not run is recorded, so absent evidence never reads as passing evidence.
- Routing is scored against reviewer labels on every push, and the build fails if a case a reviewer would have stopped is cleared automatically.
