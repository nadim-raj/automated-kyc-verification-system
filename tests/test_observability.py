import json
import unittest

from kyc_pipeline.observability import (
    PipelineMetrics,
    emit,
    log_record,
    observe,
    personal_data_leaks,
    reason_code,
)
from kyc_pipeline.orchestrator import Orchestrator
from kyc_pipeline.providers import load_case
from kyc_pipeline.synthetic import generate

SALT = "unit-test-salt"


def routed():
    orchestrator = Orchestrator()
    return [(c, orchestrator.evaluate(c)) for c in (load_case(p) for p in generate())]


class ReasonCodeTests(unittest.TestCase):
    def test_strips_score_and_detail(self):
        self.assertEqual(reason_code("name_match scored 0.47 against 0.93 (fuzzy similarity)"), "name_match")

    def test_leaves_coverage_gaps_readable(self):
        reason = "this provider supplies video, but none was attached to the case"
        self.assertEqual(reason_code(reason), reason)


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.metrics = PipelineMetrics()
        for case, decision in routed():
            self.metrics.record(case, decision)

    def test_counts_every_case(self):
        self.assertEqual(self.metrics.cases, len(generate()))

    def test_escalation_rate_matches_outcomes(self):
        cleared = self.metrics.outcomes.get("auto_clear", 0)
        self.assertAlmostEqual(self.metrics.escalation_rate, (self.metrics.cases - cleared) / self.metrics.cases)

    def test_reasons_are_grouped_by_check(self):
        self.assertIn("sole_presence", self.metrics.reasons)
        self.assertTrue(all(" scored " not in key for key in self.metrics.reasons))

    def test_unavailable_signals_are_tracked(self):
        self.assertIn("video_consistency", self.metrics.unavailable)

    def test_both_providers_counted(self):
        self.assertEqual(set(self.metrics.providers), {"video_capable", "data_only"})

    def test_empty_metrics_are_safe(self):
        self.assertEqual(PipelineMetrics().escalation_rate, 0.0)


class LogRecordTests(unittest.TestCase):
    def setUp(self):
        self.pairs = routed()

    def test_record_is_serialisable_and_single_line(self):
        case, decision = self.pairs[0]
        line = emit(log_record(case, decision, salt=SALT))
        self.assertNotIn("\n", line)
        json.loads(line)

    def test_no_case_leaks_personal_data(self):
        for case, decision in self.pairs:
            with self.subTest(case=case.case_id):
                self.assertEqual(personal_data_leaks(log_record(case, decision, salt=SALT), case), [])

    def test_the_guard_catches_a_leak_when_one_exists(self):
        case, decision = self.pairs[0]
        record = dict(log_record(case, decision, salt=SALT))
        record["debug_name"] = case.claim.full_name
        self.assertIn("claim_name", personal_data_leaks(record, case))

    def test_record_keeps_what_on_call_needs(self):
        case, decision = self.pairs[0]
        record = log_record(case, decision, salt=SALT)
        for key in ("outcome", "reason_codes", "scores", "unavailable", "provider", "case_ref"):
            self.assertIn(key, record)

    def test_case_ref_is_stable_and_salted(self):
        case, decision = self.pairs[0]
        first = log_record(case, decision, salt=SALT)["case_ref"]
        self.assertEqual(first, log_record(case, decision, salt=SALT)["case_ref"])
        self.assertNotEqual(first, log_record(case, decision, salt="other-salt")["case_ref"])


class ObserveTests(unittest.TestCase):
    def test_returns_metrics_and_one_line_per_case(self):
        pairs = routed()
        metrics, lines = observe(pairs, salt=SALT)
        self.assertEqual(metrics.cases, len(pairs))
        self.assertEqual(len(lines), len(pairs))


if __name__ == "__main__":
    unittest.main()
