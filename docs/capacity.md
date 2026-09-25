# Capacity and cost

Calibration answers what a threshold does to routing. This answers what it costs.

```bash
make capacity
python3 -m kyc_pipeline.capacity --daily-cases 5000 --minutes-per-review 6 --reviewers 8
```

## The two numbers worth arguing about

**The sustainable escalation rate.** Given daily volume, average review time and the team you have, there is a rate above which the queue grows every day. Below it the team finishes what arrives; above it no amount of effort inside the team catches up, because the shortfall compounds. That number, not a threshold, is what a staffing conversation should open with.

**The cost of each band setting.** The calibration sweep says moving a band changes the escalation rate. This prices that change in people: tightening `name_auto_clear` from 0.90 to 1.00 does not "raise escalations by 19 points", it costs sixteen more reviewers at 5,000 cases a day. Those are the same fact, but only one of them can be argued about in a budget meeting.

## What the model assumes

Every assumption here flatters the answer, so the reviewer counts it produces are a **floor**:

- Every available hour is spent reviewing. No handovers, no training, no second-line escalations.
- Every case takes the average. Real handling time has a long tail, and the queue is set by the tail, not the mean.
- Arrivals are even. They are not: verification traffic follows sign-up traffic, which peaks.
- Nobody is absent, and nobody is new.

A plan built on the raw number will be short-staffed. Treat the output as the minimum the arithmetic allows, then add whatever the deployment's reality demands.

## About the sample output

The synthetic fixtures escalate at 45%, because five of eleven were written specifically to need a human. That is an adversarial test set, not a plausible operating point, and at 5,000 cases a day it would demand a team most firms do not have.

The number to take from the sample is not the rate. It is that the join works: every point on a calibration curve can carry a staffing cost, and that is what turns a threshold discussion into a decision.

## Using it for real

1. Measure the inputs rather than estimating them. Average handling time in particular is usually worse than anyone's guess, and it is the term the whole model turns on.
2. Run the sweep, price it, and find the loosest band that misses no escalation **and** stays inside the sustainable rate. If no setting satisfies both, that is the finding: the choice is between hiring and accepting risk, and it should be made explicitly rather than absorbed by a queue.
3. Re-run it when volume changes. A rate that was comfortable at one volume is not at three times that, and nothing in the pipeline will tell you — the escalation *rate* looks identical while the queue quietly becomes unclearable.
4. Watch handling time as closely as the rate. Automation tends to clear the easy cases first, which raises the average difficulty of what reaches a human. The queue gets shorter and slower at the same time.

## Where this connects

- [Calibration](calibration.md) produces the sweep this prices.
- [Evaluation](evaluation.md) supplies the missed-escalation column, so a cheaper setting that lets cases through is visible as cheap *and* unsafe in the same table.
- [The runbook](runbook.md) covers what to do when the queue grows anyway.
