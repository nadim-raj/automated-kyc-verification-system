# Reviewer workflow

The automation exists to make a human queue smaller, not to replace it. This describes the loop the humans are in, and how their decisions feed back into the thing that decides what reaches them.

## What a reviewer receives

A packet, not a case file. It leads with why the case is in front of them — the checks that fell outside their band, in plain language — then the supporting evidence. Ordering matters: a queue of cases without stated reasons trains reviewers to start from scratch every time, which is the expensive part of the job.

The packet carries full case data. Telemetry does not. That split is deliberate: reviewers need identities to do the work, and logs, dashboards and error trackers never do.

## What a reviewer can and cannot do

**Can:** clear, decline, or ask for more evidence. Declining is a human decision — the pipeline never takes it ([decision 0002](decisions/0002-clear-or-escalate-never-auto-decline.md)).

**Cannot:** change routing. A reviewer who keeps seeing the same needless escalation should be able to say so easily, and that feedback should change a threshold through the normal process, not through an override that leaves no trace.

## The loop that keeps the gate honest

Reviewer decisions are the labels the evaluation gate scores against. That makes the loop:

1. The pipeline routes; reviewers decide.
2. Their decisions become labels on a sampled set of cases.
3. The evaluation gate scores routing against those labels on every push.
4. Calibration prices any proposed change, and capacity prices it in people.

Two things keep step 2 from rotting:

**Sample the cleared cases too.** Routing a small random share of auto-cleared cases to reviewers anyway is the only way to measure the error that matters — cases cleared that should not have been. Without it the labelled set only ever contains cases the pipeline already found suspicious, and agreement on auto-cleared cases becomes unmeasurable.

**Treat disagreement as information.** When a reviewer clears something the pipeline escalated, that is a data point about the threshold, not a reviewer error. When they escalate something the pipeline cleared, that is a defect.

## What reviewers should be measured on

Not throughput. Throughput on this queue improves by rushing, and rushing on identity work is the failure mode.

Better: agreement with a second reviewer on a sampled subset, and how often their stated reason matches what a re-review finds. Both measure judgement rather than speed, and both survive the queue getting harder — which it will, because automation clears the easy cases first and leaves the ambiguous ones behind.
