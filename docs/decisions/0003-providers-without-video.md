# 0003 — Providers that supply no video

**Status:** accepted

## Context

Verification providers differ in what they return. Some record a video of the applicant; others return documents and stills only. A pipeline that assumes video exists cannot use the second kind at all.

## Decision

Model provider capability explicitly (`ProviderKind`), and let policy decide what may be cleared with the evidence that exists. `allow_text_only_auto_clear` governs whether a case with no video can clear on documents and stills alone.

## Consequences

- **Both provider shapes work**, through one adapter each, with no branching in the pipeline.
- **The trade-off is explicit.** Clearing without video is a weaker check, and the policy flag says so in one place rather than being implied by the absence of a check.
- **Missing evidence is a stated reason.** When a video-capable provider returns no video, the case escalates with exactly that explanation, rather than silently passing the checks that happen to be available.
- **Per-provider policy is possible** without touching the orchestrator.
