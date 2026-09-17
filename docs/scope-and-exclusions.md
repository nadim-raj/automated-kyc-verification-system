# Scope and exclusions

This repository demonstrates the architecture and engineering of an automated verification pipeline. Several things are deliberately absent.

## Not included, and why

| Excluded | Reason |
|---|---|
| Production code and configuration | It belongs to the employer, not to me. |
| Trained weights | Same, and a face-recognition model is not mine to redistribute. |
| Calibrated thresholds | A published threshold on a fraud control is a published instruction for staying just underneath it. The values in `policy.py` are placeholders for the demo. |
| Detection heuristics beyond the obvious | Same reasoning. What remains follows from the problem statement itself. |
| Provider names, payload formats, quirks | Commercial relationships are not mine to describe, and vendor-specific behaviour is not the interesting part. |
| Performance figures | Real rates would describe a specific deployment. See [evaluation](evaluation.md) for how to measure your own. |
| Real data of any kind | Every fixture is invented. |

## What is included

The parts that are actually transferable: how the stages fit together, how signals stay separable and explainable, how models sit behind interfaces so the pipeline is testable without them, how missing evidence is treated differently from failing evidence, how the human review path is designed, and how personal data is kept out of telemetry.

## On publishing fraud-control work at all

There is a real tension between showing your work and handing somebody a bypass manual. The resolution used here: publish the shape of the system and the reasoning behind it, withhold the parameters and the detection specifics. Anyone evaluating this as engineering work has what they need; anyone hoping to find the edge of a live control does not.
