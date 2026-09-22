# Evaluation

An automation that clears identity checks needs to be measured before it is trusted, and kept measured afterwards. No figures appear here: the numbers that matter belong to whoever deploys it.

## Start in shadow mode

Run the pipeline alongside the manual process without acting on its output. Reviewers keep deciding; the pipeline records what it would have done. That produces a labelled sample at no risk, and it answers the only question worth asking at the start: on the cases the pipeline would have cleared, what did a human actually decide?

## What to measure

| Measure | Question it answers |
|---|---|
| Agreement on auto-cleared cases | Of the cases the pipeline would clear, how many did reviewers also clear? This is the number that governs whether automation is safe to switch on. |
| Escalation rate | What share of cases still reach a human? This governs whether it is worth switching on. |
| Reason precision | When the pipeline escalates, was the stated reason the one the reviewer acted on? Wrong reasons train reviewers to ignore them. |
| Per-signal error analysis | Which check produces the most disagreements, and on which kinds of names or documents? |
| Reviewer time per case | Does a pre-explained queue actually reduce handling time, or just move the work? |

## Slice before you conclude

An aggregate agreement figure can hide a check that works for one naming convention and fails for another. Slice by document type, by market, and by name structure, and look at the worst slice rather than the mean. A pipeline that works for most customers and reliably fails one group is not a working pipeline.

## Keep measuring

- **Sample continuously.** Route a small random share of auto-cleared cases to reviewers anyway, and watch agreement over time.
- **Watch the score distributions.** A shift in the spread of a signal usually means the input changed — a new document format, a new provider version — before any accuracy metric moves.
- **Re-check after every threshold change**, and treat threshold changes as releases, not configuration tweaks.

## Running it

```bash
make eval
```

`kyc_pipeline/evaluation.py` routes every labelled case and compares the result against what a reviewer decided, reporting the two errors separately:

| Reported | Meaning |
|---|---|
| **Missed escalation** | Cleared automatically when a reviewer would have stopped it. The error that lets something through. |
| **Unnecessary escalation** | Sent to a human who cleared it anyway. The error that wastes the time automation was meant to save. |
| Agreement on auto-cleared | Share of auto-cleared cases a reviewer would also have cleared — the number that governs whether automation is safe to enable. |
| Escalation rate | Share of cases still reaching a human — the number that governs whether it is worth enabling. |

It also breaks escalations down by the check that caused them and by provider, because an aggregate can hide one provider or one check doing badly.

Labels live in `data/synthetic/labels.json`, separate from the cases, mirroring reality: labels come from reviewers long after the case arrives.

**The command exits non-zero on any missed escalation**, and CI runs it on every push. A change that starts clearing cases a reviewer would stop fails the build rather than shipping quietly.

## Testing the code

The test suite runs on the synthetic fixtures, which cover the harmless variations that must not be escalated (transliteration, name ordering, missing middle names, confusable glyphs) and the situations that must be (transposed dates, a second face in frame, a different person in the video, media that never arrived). These are correctness tests for routing logic, not accuracy measurements — no synthetic sample tells you how a model behaves on real faces.
