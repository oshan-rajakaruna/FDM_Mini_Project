"""Regression tests for narrow stage-verifier structural allowances."""

from pathlib import Path
import unittest

from scripts.verify_stage1 import _is_t08_out_of_scope_path


class StageVerifierTests(unittest.TestCase):
    def test_only_intended_t12_model_artifact_is_allowed(self) -> None:
        self.assertFalse(_is_t08_out_of_scope_path(Path("models")))
        self.assertFalse(
            _is_t08_out_of_scope_path(
                Path("models") / "final_rainfall_model.joblib"
            )
        )
        for unexpected in (
            Path("models") / "anything_else.joblib",
            Path("models") / "debug",
            Path("models") / "debug" / "trace.txt",
            Path("models") / "temp.txt",
        ):
            with self.subTest(path=unexpected):
                self.assertTrue(_is_t08_out_of_scope_path(unexpected))


if __name__ == "__main__":
    unittest.main()
