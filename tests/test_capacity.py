import unittest

from kyc_pipeline.calibration import sweep_band
from kyc_pipeline.capacity import (
    ReviewCapacity,
    main,
    price_sweep,
    reviewers_for,
    sustainable_escalation_rate,
    workload,
)
from kyc_pipeline.evaluation import load_labels
from kyc_pipeline.providers import load_case
from kyc_pipeline.synthetic import generate


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.capacity = ReviewCapacity(daily_cases=1000, minutes_per_review=6, reviewer_hours_per_day=6, reviewers=2)

    def test_hours_available(self):
        self.assertEqual(self.capacity.hours_available, 12)

    def test_rejects_impossible_inputs(self):
        with self.assertRaises(ValueError):
            ReviewCapacity(minutes_per_review=0)
        with self.assertRaises(ValueError):
            ReviewCapacity(reviewer_hours_per_day=0)

    def test_workload_scales_with_rate(self):
        light = workload(self.capacity, 0.1)
        heavy = workload(self.capacity, 0.2)
        self.assertAlmostEqual(heavy.hours_required, light.hours_required * 2)

    def test_workload_maths(self):
        load = workload(self.capacity, 0.1)
        self.assertAlmostEqual(load.escalations_per_day, 100)
        self.assertAlmostEqual(load.hours_required, 10.0)

    def test_sustainable_when_inside_capacity(self):
        self.assertTrue(workload(self.capacity, 0.1).sustainable)

    def test_not_sustainable_beyond_capacity(self):
        load = workload(self.capacity, 0.5)
        self.assertFalse(load.sustainable)
        self.assertGreater(load.backlog_growth_per_day, 0)

    def test_backlog_growth_is_zero_when_sustainable(self):
        self.assertEqual(workload(self.capacity, 0.05).backlog_growth_per_day, 0.0)

    def test_rate_must_be_a_proportion(self):
        with self.assertRaises(ValueError):
            workload(self.capacity, 1.5)

    def test_sustainable_rate_matches_available_hours(self):
        self.assertAlmostEqual(sustainable_escalation_rate(self.capacity), 0.12)

    def test_sustainable_rate_caps_at_one(self):
        generous = ReviewCapacity(daily_cases=10, minutes_per_review=1, reviewer_hours_per_day=8, reviewers=10)
        self.assertEqual(sustainable_escalation_rate(generous), 1.0)

    def test_reviewers_round_up(self):
        self.assertEqual(reviewers_for(self.capacity, 0.1), 2)


class PricedSweepTests(unittest.TestCase):
    def setUp(self):
        self.cases = [load_case(p) for p in generate()]
        self.labels = load_labels()

    def test_each_point_carries_a_staffing_cost(self):
        sweep = sweep_band("name_auto_clear", self.cases, self.labels, values=(0.5, 0.95, 1.0))
        priced = price_sweep(sweep, ReviewCapacity(), len(self.cases))
        self.assertEqual(len(priced), 3)
        for row in priced:
            self.assertIn("reviewers_required", row)

    def test_tighter_band_never_costs_fewer_reviewers(self):
        sweep = sweep_band("name_auto_clear", self.cases, self.labels, values=(0.5, 1.0))
        loose, tight = price_sweep(sweep, ReviewCapacity(), len(self.cases))
        self.assertGreaterEqual(tight["reviewers_required"], loose["reviewers_required"])

    def test_cli_runs(self):
        self.assertEqual(main(["--daily-cases", "1000", "--reviewers", "4"]), 0)


if __name__ == "__main__":
    unittest.main()
