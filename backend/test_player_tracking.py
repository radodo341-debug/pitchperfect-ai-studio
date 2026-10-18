import os
import tempfile
import unittest
from unittest.mock import patch

from player_tracking import sample_video, tracking_status


class PlayerTrackingTests(unittest.TestCase):
    def test_tracking_status_is_explicit_when_unconfigured(self):
        with patch.dict(os.environ, {"PP_TRACKER_MODEL": ""}, clear=False):
            status = tracking_status()
        self.assertFalse(status["configured"])
        self.assertIn("anonymous", status["identity_mode"])

    def test_rejects_invalid_sampling_rate(self):
        with self.assertRaises(ValueError):
            sample_video("unused.mp4", sample_fps=0)

    def test_missing_model_fails_clearly(self):
        with patch.dict(os.environ, {"PP_TRACKER_MODEL": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                sample_video("unused.mp4")


if __name__ == "__main__":
    unittest.main()
