# Privacy

Identity verification handles precisely the data you least want leaking: government identifiers, faces, dates of birth. The design choices below follow from that.

## Minimise what moves

The pipeline reads what it needs to score a case and passes on a decision. Images and video are referenced by URI rather than carried through the call stack, so media never lands in an unexpected process.

## Separate reviewers from telemetry

Reviewers need the real values to do their job. Logs, metrics, and error trackers do not, and they are copied to more places than anyone tracks. `review.to_log_record` emits scores, outcomes, and masked previews; `pii.py` provides masking and salted pseudonymisation for joining records without storing the values themselves.

A hash of a national identifier is not anonymous: the space is small enough to enumerate. Pseudonymisation here is salted, and the salt is a secret that needs rotating like any other key.

## Retention

Verification media has a short useful life and a long liability. Keep decisions and scores for as long as the regulation requires; keep the media only as long as the review process needs it. The interfaces in this repository are URI-based partly so that deleting the underlying object is sufficient.

## Access

Reviewer access to full case data should be logged, attributable, and scoped to assigned cases. Nobody needs standing access to every applicant's documents.

## Automated decisions

Several jurisdictions give people a right not to be subject to solely automated decisions with significant effects, and a right to an explanation. Two design choices here follow from that:

- The pipeline never declines anyone automatically ([decision 0002](decisions/0002-clear-or-escalate-never-auto-decline.md)).
- Every escalation carries stated reasons, so a human decision has a documented starting point rather than an opaque score.

## This repository

Every case in `data/synthetic/` is invented, and the synthetic embedder derives vectors from fixture seeds rather than images. No real personal data is present, and none should be added.
