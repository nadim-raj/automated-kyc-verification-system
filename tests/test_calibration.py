import unittest

from kyc_pipeline.calibration import (
    BandSweep,
    SweepPoint,
    default_grid,
    main,
    sweep_all,
    sweep_band,
    to_dict,
)
from kyc_pipeline.evaluation import load_labels
from kyc_pipeline.policy import DecisionPolicy
from kyc_pipeline.providers import load_case
from kyc_pipeline.synthetic import generate


def point(value, escalated, missed=0):
    return SweepPoint(
        band="name_auto_clear",
        value=value,
        escalated=escalated,
        escalation_rate=escalated / 10,
        missed_escalations=missed,
        unnecessary_escalations=0,
        agreement_on_cleared=1.0,
    )


class GridTests(unittest.TestCase):
    def test_grid_spans_the_range_inclusively(self):
        grid = default_grid(0.5, 1.0, 0.1)
        self.assertEqual(grid[0], 0.5)
        self.assertEqual(grid[-1], 1.0)

    def test_grid_values_are_rounded(self):
        self.assertTrue(all(round(v, 2) == v for v in default_grid()))


class BandSweepTests(unittest.TestCase):
    def test_inert_when_no_value_changes_routing(self):
        sweep = BandSweep("b", (point(0.5, 3), point(0.9, 3)))
        self.assertTrue(sweep.is_inert)

    def test_not_inert_when_routing_moves(self):
        sweep = BandSweep("b", (point(0.5, 2), point(0.9, 5)))
        self.assertFalse(sweep.is_inert)

    def test_safe_ceiling_is_loosest_value_missing_nothing(self):
        sweep = BandSweep("b", (point(0.5, 2, missed=1), point(0.7, 3), point(0.9, 5)))
        self.assertEqual(sweep.safe_ceiling, 0.7)

    def test_safe_ceiling_is_none_when_every_value_misses(self):
        sweep = BandSweep("b", (point(0.5, 2, missed=1), point(0.9, 3, missed=1)))
        self.assertIsNone(sweep.safe_ceiling)

    def test_escalation_span(self):
        self.assertEqual(BandSweep("b", (point(0.5, 2), point(0.9, 5))).escalation_span, (2, 5))


class SweepOverFixturesTests(unittest.TestCase):
    def setUp(self):
        self.cases = [load_case(p) for p in generate()]
        self.labels = load_labels()

    def test_tightening_the_name_band_escalates_at_least_as_much(self):
        sweep = sweep_band("name_auto_clear", self.cases, self.labels, values=(0.5, 0.95))
        loose, tight = sweep.points
        self.assertGreaterEqual(tight.escalated, loose.escalated)

    def test_unknown_band_is_rejected(self):
        with self.assertRaises(ValueError):
            sweep_band("not_a_band", self.cases, self.labels, values=(0.5,))

    def test_base_policy_is_respected(self):
        strict = DecisionPolicy(allow_text_only_auto_clear=False)
        sweep = sweep_band("name_auto_clear", self.cases, self.labels, values=(0.5,), base_policy=strict)
        default = sweep_band("name_auto_clear", self.cases, self.labels, values=(0.5,))
        self.assertGreater(sweep.points[0].escalated, default.points[0].escalated)

    def test_sweep_all_covers_every_requested_band(self):
        bands = ("name_auto_clear", "face_auto_clear")
        sweeps = sweep_all(self.cases, self.labels, bands)
        self.assertEqual([s.band for s in sweeps], list(bands))

    def test_serialisable_output(self):
        sweeps = sweep_all(self.cases, self.labels, ("name_auto_clear",))
        payload = to_dict(sweeps)
        self.assertIn("name_auto_clear", payload)
        self.assertIn("points", payload["name_auto_clear"])

    def test_cli_runs(self):
        self.assertEqual(main(["--band", "name_auto_clear"]), 0)


if __name__ == "__main__":
    unittest.main()
