import unittest
from datetime import date

from kyc_pipeline.domain import DocumentExtract, IdentityClaim
from kyc_pipeline.matching import (
    date_of_birth_signal,
    document_number_signal,
    name_signal,
    score_names,
    text_signals,
)


def claim(**kwargs):
    base = dict(full_name="Arif Rahman Chowdhury", date_of_birth=date(1993, 4, 17), nationality="BGD", document_number="BP7741820")
    base.update(kwargs)
    return IdentityClaim(**base)


def document(**kwargs):
    base = dict(full_name="Arif Rahman Chowdhury", date_of_birth=date(1993, 4, 17), nationality="BGD", document_number="BP7741820")
    base.update(kwargs)
    return DocumentExtract(**base)


class NameMatchingTests(unittest.TestCase):
    def test_identical_names_score_one(self):
        score, _ = score_names("Arif Rahman Chowdhury", "Arif Rahman Chowdhury")
        self.assertEqual(score, 1.0)

    def test_order_swap_scores_high(self):
        score, detail = score_names("Chowdhury Nusrat Jahan", "Nusrat Jahan Chowdhury")
        self.assertGreaterEqual(score, 0.95)
        self.assertIn("order", detail)

    def test_missing_middle_name_scores_high(self):
        score, _ = score_names("Sadia Islam", "Sadia Akter Islam")
        self.assertGreaterEqual(score, 0.9)

    def test_unrelated_names_score_low(self):
        score, _ = score_names("Wei Ling Tan", "Siti Aminah Rahman")
        self.assertLess(score, 0.6)

    def test_empty_name_is_unavailable(self):
        signal = name_signal(claim(full_name=""), document())
        self.assertFalse(signal.available)


class FieldMatchingTests(unittest.TestCase):
    def test_matching_dates_score_one(self):
        self.assertEqual(date_of_birth_signal(claim(), document()).score, 1.0)

    def test_transposed_day_and_month_is_flagged_but_recognised(self):
        signal = date_of_birth_signal(claim(), document(date_of_birth=date(1993, 17 % 12 or 12, 4)))
        self.assertTrue(signal.available)

    def test_transposition_detected(self):
        signal = date_of_birth_signal(
            claim(date_of_birth=date(1991, 5, 8)),
            document(date_of_birth=date(1991, 8, 5)),
        )
        self.assertEqual(signal.score, 0.5)
        self.assertIn("transposed", signal.detail)

    def test_ocr_confusion_still_matches(self):
        signal = document_number_signal(claim(document_number="BP0O12345"), document(document_number="BP0012345"))
        self.assertEqual(signal.score, 1.0)

    def test_text_signals_cover_four_checks(self):
        names = {s.name for s in text_signals(claim(), document())}
        self.assertEqual(names, {"name_match", "dob_match", "document_number_match", "nationality_match"})


if __name__ == "__main__":
    unittest.main()
