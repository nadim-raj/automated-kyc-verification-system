# 0001 — Separate text and vision signals

**Status:** accepted

## Context

A verification case asks two unrelated questions. Do the submitted details match the document? And is the person doing the check the person on the document, alone? The first is a text problem — names, dates, identifiers, all of which vary in well-understood ways. The second is a vision problem.

A single model over all of it, or a single blended score, was possible. It was also the wrong shape.

## Decision

Keep the two families separate. Each comparison produces its own scored signal with its own explanation, and the orchestrator routes on the collection.

## Consequences

- **Reviewers get reasons.** "The name matched; the video shows a second person from four seconds in" is actionable. A single score of 0.62 is not.
- **Checks tune independently.** A change to name normalisation cannot silently shift the face threshold.
- **Failures stay legible.** When a check regresses, it is obvious which one.
- **More configuration surface.** Several bands instead of one. Worth it, but it is a real cost, and it is why the bands live in one policy object rather than scattered through the code.
