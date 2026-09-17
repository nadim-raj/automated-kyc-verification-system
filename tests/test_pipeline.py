import unittest

from kyc_pipeline.domain import Outcome, ProviderKind
from kyc_pipeline.orchestrator import Orchestrator
from kyc_pipeline.policy import DecisionPolicy
from kyc_pipeline.providers import load_case, parse_date
from kyc_pipeline.review import build_packet, to_log_record
from kyc_pipeline.synthetic import SCENARIOS, generate


def evaluate_all(orchestrator=None):
    orchestrator = orchestrator or Orchestrator()
    out = {}
    for payload in generate():
        case = load_case(payload)
        out[case.case_id] = (case, orchestrator.evaluate(case))
    return out


class ProviderAdapterTests(unittest.TestCase):
    def test_parses_several_date_formats(self):
        self.assertEqual(parse_date("1993-04-17"), parse_date("17/04/1993"))
        self.assertIsNone(parse_date("not a date"))

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            load_case({"provider": "mystery"})

    def test_both_providers_produce_cases(self):
        kinds = {case.provider for case, _ in evaluate_all().values()}
        self.assertEqual(kinds, {ProviderKind.VIDEO_CAPABLE, ProviderKind.DATA_ONLY})


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.results = evaluate_all()

    def test_every_scenario_is_covered(self):
        self.assertEqual(set(self.results), set(SCENARIOS))

    def test_clean_case_clears_without_a_reviewer(self):
        _, decision = self.results["clean_video_match"]
        self.assertEqual(decision.outcome, Outcome.AUTO_CLEAR)
        self.assertEqual(decision.reasons, ())

    def test_harmless_variations_still_clear(self):
        for scenario in ("transliteration_variant", "name_order_swapped", "document_number_ocr_confusion"):
            with self.subTest(scenario=scenario):
                self.assertEqual(self.results[scenario][1].outcome, Outcome.AUTO_CLEAR)

    def test_second_person_in_frame_is_escalated(self):
        _, decision = self.results["second_person_in_frame"]
        self.assertEqual(decision.outcome, Outcome.REVIEW)
        self.assertTrue(any("sole_presence" in reason for reason in decision.reasons))

    def test_different_person_in_video_is_escalated(self):
        _, decision = self.results["different_person_in_video"]
        self.assertEqual(decision.outcome, Outcome.REVIEW)
        self.assertTrue(any("video_consistency" in reason for reason in decision.reasons))

    def test_transposed_date_is_escalated(self):
        self.assertEqual(self.results["dob_day_month_transposed"][1].outcome, Outcome.REVIEW)

    def test_missing_video_from_video_provider_is_escalated(self):
        _, decision = self.results["video_expected_but_absent"]
        self.assertEqual(decision.outcome, Outcome.REVIEW)
        self.assertTrue(any("video" in reason for reason in decision.reasons))

    def test_data_only_provider_can_clear_on_documents_alone(self):
        self.assertEqual(self.results["data_only_clean"][1].outcome, Outcome.AUTO_CLEAR)

    def test_data_only_name_mismatch_is_escalated(self):
        self.assertEqual(self.results["data_only_name_mismatch"][1].outcome, Outcome.REVIEW)

    def test_media_can_be_required_by_policy(self):
        strict = Orchestrator(policy=DecisionPolicy(allow_text_only_auto_clear=False))
        results = evaluate_all(strict)
        self.assertEqual(results["data_only_clean"][1].outcome, Outcome.REVIEW)

    def test_nothing_is_declined_automatically_by_default(self):
        outcomes = {decision.outcome for _, decision in self.results.values()}
        self.assertNotIn(Outcome.DECLINE, outcomes)


class ReviewPacketTests(unittest.TestCase):
    def test_packet_leads_with_the_first_failing_check(self):
        case, decision = evaluate_all()["different_person_in_video"]
        packet = build_packet(case, decision)
        self.assertIn("need a look", packet.headline)
        self.assertTrue(packet.checks)

    def test_log_record_carries_no_raw_personal_data(self):
        case, decision = evaluate_all()["clean_video_match"]
        record = to_log_record(case, decision, salt="unit-test-salt")
        serialised = str(record)
        self.assertNotIn(case.claim.full_name, serialised)
        self.assertNotIn(case.document.document_number or "", serialised)
        self.assertIn("outcome", record)


if __name__ == "__main__":
    unittest.main()
