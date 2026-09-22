import unittest

from kyc_pipeline.evaluation import (
    CaseResult,
    Evaluation,
    evaluate,
    load_cases,
    load_labels,
    main,
)
from kyc_pipeline.orchestrator import Orchestrator
from kyc_pipeline.policy import DecisionPolicy
from kyc_pipeline.synthetic import generate
from kyc_pipeline.providers import load_case


def result(case_id, pipeline, reviewer, reasons=()):
    return CaseResult(
        case_id=case_id,
        provider="video_capable",
        pipeline_outcome=pipeline,
        reviewer_outcome=reviewer,
        reasons=tuple(reasons),
    )


class ErrorTypeTests(unittest.TestCase):
    def test_missed_escalation_is_cleared_when_reviewer_would_stop(self):
        r = result("a", "auto_clear", "escalate")
        self.assertTrue(r.missed_escalation)
        self.assertFalse(r.unnecessary_escalation)
        self.assertFalse(r.agrees)

    def test_unnecessary_escalation_costs_reviewer_time(self):
        r = result("b", "review", "clear")
        self.assertTrue(r.unnecessary_escalation)
        self.assertFalse(r.missed_escalation)

    def test_agreement_both_ways(self):
        self.assertTrue(result("c", "auto_clear", "clear").agrees)
        self.assertTrue(result("d", "review", "escalate").agrees)


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.evaluation = Evaluation(results=[
            result("cleared-ok", "auto_clear", "clear"),
            result("cleared-bad", "auto_clear", "escalate"),
            result("escalated-ok", "review", "escalate", ["name_match scored 0.40 against 0.93 (fuzzy)"]),
            result("escalated-waste", "review", "clear", ["dob_match scored 0.50 against 1.00 (transposed)"]),
        ])

    def test_counts(self):
        self.assertEqual(self.evaluation.total, 4)
        self.assertEqual(len(self.evaluation.cleared), 2)
        self.assertEqual(len(self.evaluation.escalated), 2)

    def test_agreement_on_cleared_excludes_escalated_cases(self):
        self.assertAlmostEqual(self.evaluation.agreement_on_cleared, 0.5)

    def test_overall_agreement(self):
        self.assertAlmostEqual(self.evaluation.overall_agreement, 0.5)

    def test_escalation_rate(self):
        self.assertAlmostEqual(self.evaluation.escalation_rate, 0.5)

    def test_reason_frequency_strips_scores(self):
        reasons = dict(self.evaluation.reason_frequency())
        self.assertIn("name_match", reasons)
        self.assertIn("dob_match", reasons)

    def test_empty_evaluation_is_safe(self):
        empty = Evaluation()
        self.assertEqual(empty.total, 0)
        self.assertEqual(empty.agreement_on_cleared, 1.0)
        self.assertEqual(empty.escalation_rate, 0.0)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.labels = load_labels()
        self.cases = [load_case(p) for p in generate()]

    def test_every_fixture_has_a_label(self):
        unlabelled = [c.case_id for c in self.cases if c.case_id not in self.labels]
        self.assertEqual(unlabelled, [])

    def test_pipeline_misses_no_escalation_on_the_fixtures(self):
        evaluation = evaluate(self.cases, self.labels)
        self.assertEqual([r.case_id for r in evaluation.missed_escalations], [])

    def test_stricter_policy_raises_escalation_rate(self):
        default = evaluate(self.cases, self.labels)
        strict = evaluate(
            self.cases,
            self.labels,
            Orchestrator(policy=DecisionPolicy(allow_text_only_auto_clear=False)),
        )
        self.assertGreater(strict.escalation_rate, default.escalation_rate)

    def test_unlabelled_cases_are_skipped_not_guessed(self):
        evaluation = evaluate(self.cases, {"clean_video_match": "clear"})
        self.assertEqual(evaluation.total, 1)

    def test_cli_exits_zero_when_nothing_is_missed(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
