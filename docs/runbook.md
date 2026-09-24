# Runbook

What to do when the pipeline misbehaves. Written for whoever is on call, including me at 3am, which is why every entry says what *not* to do as well.

The governing principle: **this pipeline is allowed to stop clearing cases, and is never allowed to start clearing the wrong ones.** When in doubt, route everything to humans and take the reviewer backlog. A queue is a staffing problem; a wrongly cleared identity is not recoverable.

---

## Escalation rate jumps

**Symptom.** The share of cases reaching reviewers climbs sharply; the queue grows.

**Usually means.** An input changed, not the pipeline. A provider altered a payload field, a document type started arriving differently, or a new market brought naming conventions the normalisation rules do not cover.

**Check.**
```bash
python3 -m kyc_pipeline.evaluation          # which checks are sending cases to humans
```
Compare `escalation_reasons` against a normal window. One check dominating points at input drift; a flat rise across all checks points at something upstream of the pipeline.

**Do.** Let it escalate. Find the input change, fix the handling, and re-run the evaluation before touching any threshold.

**Do not** loosen a band to drain the queue. That converts a visible backlog into invisible risk, and the threshold rarely gets tightened again.

---

## Escalation rate falls

**Symptom.** Reviewer volume drops and nobody complains.

**Usually means.** Something stopped running. A media check silently unavailable, a provider no longer sending video, or a deploy that changed policy defaults.

**Check.** `unavailable_signals` in the metrics. A check that used to run and now does not is the first suspect. This is exactly why unavailable checks are recorded as signals rather than omitted.

**Do.** Treat a quiet drop as an incident, not good news. Verify the evaluation gate still passes, then confirm the provider is still sending what it used to.

---

## The face model is unavailable

**Symptom.** Face checks failing or erroring for every case.

**Usually means.** The model host is down, weights failed to load, or a deploy shipped a bad embedder configuration.

**Do.** Fail closed: cases with no usable face evidence escalate, because the media checks are unavailable and the coverage gap is reported as a reason. Confirm the queue is absorbing them and staff accordingly.

**Do not** fall back to text-only auto-clearing for a video-capable provider as a workaround. If that trade-off is ever acceptable it is a policy decision, made deliberately with `allow_text_only_auto_clear`, not an incident-time improvisation.

---

## A provider payload changes shape

**Symptom.** Adapter errors, or a sudden rise in unavailable signals for one provider.

**Usually means.** A vendor schema change. Fields get renamed, dates change format, media moves.

**Check.** Provider counts in the metrics and the `unavailable` list per provider. One provider behaving differently from the other localises it immediately.

**Do.** Fix the adapter, add a fixture that covers the new shape, and only then redeploy. Adapters are the one place vendor-specific handling belongs; nothing downstream should learn about the change.

---

## CI fails on the evaluation gate

**Symptom.** `python -m kyc_pipeline.evaluation` exits non-zero: a case a reviewer would have stopped was cleared automatically.

**Usually means.** A change loosened routing, or altered matching so a failing case now passes.

**Do.** Treat it as a blocking defect. Find which case flipped, decide whether the pipeline or the label is wrong, and fix whichever it is. If the label is wrong, change the label deliberately and say so in the commit.

**Do not** pass `--allow-missed-escalations` to get a build green. The flag exists for local exploration. Using it in CI removes the only automated protection against the failure mode that matters.

---

## Reviewer backlog grows faster than it drains

**Symptom.** Cases age; time-to-decision climbs.

**Usually means.** A capacity problem, not a pipeline problem — unless one of the entries above is the cause.

**Do.** Rule out a routing change first, because a threshold move is cheap to reverse and staffing is not. Once routing is confirmed unchanged, this is a staffing conversation, held with the escalation rate and the review time per case in hand.

---

## Personal data appears in logs

**Symptom.** A name, document number or date of birth visible in a log line or an error report.

**Do.** Treat it as a data incident: stop the deploy, purge where the logs landed, and add the field to the guard. `observability.personal_data_leaks` asserts this in the test suite specifically so a new field cannot introduce it quietly. If it escaped anyway, the guard has a gap worth closing in the same fix.
