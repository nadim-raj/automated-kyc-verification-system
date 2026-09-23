# Calibration

The bands in `policy.py` are placeholders. This page is about the method for replacing them, and what that method already reveals.

```bash
make calibrate
```

## How the sweep works

Each band is moved across a range on its own, with every other band held at its default. At each step the pipeline re-routes every labelled case and the result is scored against what a reviewer decided. Four numbers come back per step:

| Column | Meaning |
|---|---|
| escalated | How many cases reach a human at this setting |
| missed | Cases cleared automatically that a reviewer would have stopped |
| wasted | Cases sent to a human who cleared them anyway |
| agreement | Share of auto-cleared cases a reviewer would also have cleared |

The shape is always the same trade-off. Tighten a band and reviewer workload rises. Loosen it and more clears automatically, until cases that should have been stopped start slipping through. Calibration is choosing where on that curve to sit, with the cost of each error in view.

## What the current fixtures say

Two findings, both about the test data rather than the thresholds:

**Loosening any band down to 0.50 misses nothing.** That is not a licence to loosen them. It means every failing fixture fails categorically — the video is absent, or the person in it is somebody else entirely — rather than marginally. There is no case that sits near a boundary, so the sweep has nothing to bite on below the defaults.

**Tightening is where the fixtures react.** Pushing a band to 1.00 escalates clean cases: transliteration variants, a missing middle name, a zero read as the letter O. That side of the curve is well covered, because those are exactly the cases the normalisation work exists to absorb.

**Some bands are inert.** Every value routes identically, meaning no fixture depends on them at all. The report names them rather than drawing a flat line, because a band nothing exercises is a gap in the test data, not a safe setting.

The obvious next step for the fixtures is near-threshold cases: a genuinely ambiguous name, a partially obscured face, a video where a second person appears only briefly. Those are what make a sensitivity curve worth reading.

## Doing this with real data

The tool is the method; the data has to be real.

1. Run in shadow mode until you have a reviewer-labelled sample that reflects actual traffic, including its awkward tail.
2. Sweep each band and read the two error columns separately. They are not interchangeable: a missed escalation is a control failure, a wasted escalation is a cost.
3. Choose the loosest setting that holds missed escalations at zero on the labelled sample, then leave headroom — a sample is not the population.
4. Slice before concluding. A band that works across most customers can fail one naming convention or one document type. Look at the worst slice, not the mean.
5. Re-sweep whenever the inputs change: a new document format, a new provider version, a new market.

Calibrated values belong in private configuration, never in this repository. A published threshold on a fraud control is a published instruction for staying just underneath it.
