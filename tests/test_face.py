import unittest

from kyc_pipeline.domain import ImageRef, MediaBundle
from kyc_pipeline.face import SyntheticEmbedder, SyntheticFaceCounter, cosine, face_match_signal, sole_presence_signal
from kyc_pipeline.face.verification import video_consistency_signal


def image(identity, capture="a", faces=None):
    payload = {"identity_seed": identity, "capture": capture}
    if faces is not None:
        payload["faces"] = faces
    return ImageRef(uri=f"s3://x/{identity}", payload=payload)


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.embedder = SyntheticEmbedder()

    def test_same_identity_scores_higher_than_different(self):
        same = cosine(self.embedder.embed(image("id-1", "a")), self.embedder.embed(image("id-1", "b")))
        different = cosine(self.embedder.embed(image("id-1", "a")), self.embedder.embed(image("id-2", "b")))
        self.assertGreater(same, different)
        self.assertGreater(same, 0.9)

    def test_embedding_is_deterministic(self):
        self.assertEqual(self.embedder.embed(image("id-1")), self.embedder.embed(image("id-1")))

    def test_no_identity_yields_no_embedding(self):
        self.assertIsNone(self.embedder.embed(ImageRef(uri="s3://x", payload={})))

    def test_cosine_is_bounded(self):
        self.assertEqual(cosine([], [1.0]), 0.0)
        self.assertLessEqual(cosine([1.0, 0.0], [1.0, 0.0]), 1.0)


class MediaSignalTests(unittest.TestCase):
    def setUp(self):
        self.embedder = SyntheticEmbedder()
        self.counter = SyntheticFaceCounter()

    def test_face_match_needs_both_images(self):
        signal = face_match_signal(MediaBundle(selfie=image("id-1")), self.embedder)
        self.assertFalse(signal.available)

    def test_face_match_scores_same_person_highly(self):
        media = MediaBundle(selfie=image("id-1", "selfie"), document_portrait=image("id-1", "portrait"))
        self.assertGreater(face_match_signal(media, self.embedder).score, 0.85)

    def test_sole_presence_detects_extra_face(self):
        frames = [image("id-1", f"f{i}", faces=["id-1"]) for i in range(8)]
        frames += [image("id-1", f"f{i}", faces=["id-1", "id-9"]) for i in range(8, 10)]
        signal = sole_presence_signal(frames, self.counter)
        self.assertAlmostEqual(signal.score, 0.8, places=4)
        self.assertIn("more than one", signal.detail)

    def test_video_consistency_reports_weakest_frame(self):
        reference = image("id-1", "portrait")
        frames = [image("id-1", f"f{i}", faces=["id-1"]) for i in range(5)]
        frames.append(image("id-9", "f5", faces=["id-9"]))
        signal = video_consistency_signal(frames, reference, self.embedder)
        self.assertLess(signal.score, 0.5)

    def test_video_consistency_without_reference_is_unavailable(self):
        self.assertFalse(video_consistency_signal([image("id-1")], None, self.embedder).available)


if __name__ == "__main__":
    unittest.main()
