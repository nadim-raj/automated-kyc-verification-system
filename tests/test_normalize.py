import unittest

from kyc_pipeline.normalize import initials, name_tokens, normalize, normalize_document_number, strip_accents


class NormalisationTests(unittest.TestCase):
    def test_strips_accents(self):
        self.assertEqual(strip_accents("José Álvarez"), "Jose Alvarez")

    def test_normalise_folds_case_and_punctuation(self):
        self.assertEqual(normalize("Md.  Kamal-Hossain"), "md kamal hossain")

    def test_drops_honorifics(self):
        self.assertEqual(name_tokens("Dr. Sadia Islam"), ("sadia", "islam"))

    def test_expands_transliteration_variants(self):
        self.assertEqual(name_tokens("Md. Kamal Hossain"), name_tokens("Mohammad Kamal Hosain"))

    def test_drops_naming_particles(self):
        self.assertEqual(name_tokens("Nurul Aina Binti Zulkifli"), ("nurul", "aina", "zulkifli"))

    def test_initials(self):
        self.assertEqual(initials(("arif", "rahman", "chowdhury")), "arc")

    def test_document_number_folds_confusable_glyphs(self):
        self.assertEqual(normalize_document_number("BP0O12345"), normalize_document_number("BP0012345"))

    def test_document_number_handles_missing(self):
        self.assertEqual(normalize_document_number(None), "")


if __name__ == "__main__":
    unittest.main()
