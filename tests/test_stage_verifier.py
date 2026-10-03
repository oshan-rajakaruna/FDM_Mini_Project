"""Regression tests for narrow stage-verifier structural allowances."""

from pathlib import Path
import unittest

from scripts.verify_stage1 import _is_t08_out_of_scope_path


class StageVerifierTests(unittest.TestCase):
    def test_only_intended_dynamic_model_artifact_paths_are_allowed(self) -> None:
        allowed = (
            Path("models"),
            Path("models") / "final_rainfall_model.joblib",
            Path("models") / "comparison",
            Path("models") / "comparison" / "logistic_regression.joblib",
            Path("models") / "comparison" / "decision_tree.joblib",
            Path("models") / "comparison" / "random_forest.joblib",
            Path("models") / "comparison" / "gradient_boosting.joblib",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertFalse(_is_t08_out_of_scope_path(path))
        for unexpected in (
            Path("models") / "anything_else.joblib",
            Path("models") / "debug",
            Path("models") / "debug" / "trace.txt",
            Path("models") / "temp.txt",
            Path("models") / "comparison" / "test.joblib",
            Path("models") / "comparison" / "random.txt",
        ):
            with self.subTest(path=unexpected):
                self.assertTrue(_is_t08_out_of_scope_path(unexpected))


if __name__ == "__main__":
    unittest.main()
