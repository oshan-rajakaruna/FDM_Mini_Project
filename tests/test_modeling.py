"""Focused tests for T09 validation-only baseline modeling."""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.modeling import (  # noqa: E402
    METRIC_COLUMNS,
    MODEL_NAMES,
    RANDOM_STATE,
    build_baseline_models,
    calculate_binary_metrics,
    confusion_counts,
    fit_and_evaluate_baselines,
    positive_class_probability,
)


def synthetic_processed_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    rng = np.random.default_rng(42)
    train_values = rng.normal(size=(80, 5))
    validation_values = rng.normal(size=(24, 5))
    train_score = train_values[:, 0] + 0.5 * train_values[:, 1]
    validation_score = validation_values[:, 0] + 0.5 * validation_values[:, 1]
    X_train = pd.DataFrame(train_values, columns=[f"f{i}" for i in range(5)], index=range(80))
    X_validation = pd.DataFrame(
        validation_values,
        columns=X_train.columns,
        index=range(100, 124),
    )
    y_train = pd.Series(np.where(train_score > 0, "Yes", "No"), index=X_train.index)
    y_validation = pd.Series(
        np.where(validation_score > 0, "Yes", "No"),
        index=X_validation.index,
    )
    return X_train, X_validation, y_train, y_validation


class BaselineModelingTests(unittest.TestCase):
    def test_exactly_four_required_model_types_are_configured(self) -> None:
        models = build_baseline_models()
        self.assertEqual(tuple(models), MODEL_NAMES)
        self.assertEqual(len(models), 4)
        self.assertIsInstance(models["Logistic Regression"], LogisticRegression)
        self.assertIsInstance(models["Decision Tree"], DecisionTreeClassifier)
        self.assertIsInstance(models["Random Forest"], RandomForestClassifier)
        self.assertIsInstance(models["Gradient Boosting"], GradientBoostingClassifier)

    def test_execution_only_configuration_is_reproducible(self) -> None:
        models = build_baseline_models()
        for model in models.values():
            self.assertEqual(model.get_params()["random_state"], RANDOM_STATE)
        self.assertEqual(models["Logistic Regression"].max_iter, 1000)
        self.assertEqual(models["Random Forest"].n_jobs, -1)
        self.assertEqual(models["Random Forest"].n_estimators, 100)
        self.assertIsNone(models["Decision Tree"].max_depth)
        self.assertEqual(models["Gradient Boosting"].n_estimators, 100)

    def test_positive_probability_uses_class_label_not_fixed_column(self) -> None:
        class ReversedProbabilityModel:
            classes_ = np.array(["Yes", "No"])

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                return np.tile([0.8, 0.2], (len(X), 1))

        values = positive_class_probability(ReversedProbabilityModel(), pd.DataFrame({"x": [1, 2]}))
        np.testing.assert_allclose(values, [0.8, 0.8])

    def test_missing_positive_class_is_rejected(self) -> None:
        class OneClassModel:
            classes_ = np.array(["No"])

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                return np.ones((len(X), 1))

        with self.assertRaisesRegex(ValueError, "absent or ambiguous"):
            positive_class_probability(OneClassModel(), pd.DataFrame({"x": [1]}))

    def test_metrics_and_confusion_order_match_known_example(self) -> None:
        y_true = pd.Series(["No", "No", "Yes", "Yes"])
        y_pred = pd.Series(["No", "Yes", "No", "Yes"])
        probability = pd.Series([0.1, 0.8, 0.4, 0.9])
        metrics = calculate_binary_metrics(y_true, y_pred, probability)

        self.assertEqual(confusion_counts(y_true, y_pred), {"TN": 1, "FP": 1, "FN": 1, "TP": 1})
        self.assertEqual([metrics[name] for name in ("TN", "FP", "FN", "TP")], [1, 1, 1, 1])
        self.assertAlmostEqual(metrics["Accuracy"], 0.5)
        self.assertAlmostEqual(metrics["Balanced Accuracy"], 0.5)
        self.assertAlmostEqual(metrics["Precision (Yes)"], 0.5)
        self.assertAlmostEqual(metrics["Recall (Yes)"], 0.5)
        self.assertAlmostEqual(metrics["F1 (Yes)"], 0.5)
        self.assertAlmostEqual(metrics["ROC-AUC"], 0.75)
        self.assertAlmostEqual(metrics["PR-AUC"], 5 / 6)

    def test_metric_outputs_are_finite_and_valid(self) -> None:
        metrics = calculate_binary_metrics(
            pd.Series(["No", "No", "Yes", "Yes"]),
            pd.Series(["No", "No", "No", "No"]),
            pd.Series([0.1, 0.2, 0.3, 0.4]),
        )
        for name in METRIC_COLUMNS[:7]:
            self.assertTrue(np.isfinite(metrics[name]))
            self.assertGreaterEqual(metrics[name], 0)
            self.assertLessEqual(metrics[name], 1)

    def test_suite_fits_train_and_evaluates_validation_without_mutation(self) -> None:
        X_train, X_validation, y_train, y_validation = synthetic_processed_data()
        originals = [item.copy(deep=True) for item in (X_train, X_validation, y_train, y_validation)]
        lightweight_models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Decision Tree": DecisionTreeClassifier(random_state=42),
            "Random Forest": RandomForestClassifier(
                n_estimators=5,
                random_state=42,
                n_jobs=1,
            ),
            "Gradient Boosting": GradientBoostingClassifier(
                n_estimators=5,
                random_state=42,
            ),
        }
        with patch("fdm_rainfall.modeling.build_baseline_models", return_value=lightweight_models):
            evaluation = fit_and_evaluate_baselines(
                X_train,
                X_validation,
                X_train,
                X_validation,
                y_train,
                y_validation,
            )

        self.assertEqual(evaluation.comparison["Model"].tolist(), list(MODEL_NAMES))
        self.assertEqual(evaluation.comparison.columns.tolist(), ["Model", *METRIC_COLUMNS])
        for model in evaluation.fitted_models.values():
            self.assertEqual(int(model.n_features_in_), X_train.shape[1])
        for name in MODEL_NAMES:
            self.assertEqual(len(evaluation.predictions[name]), len(y_validation))
            self.assertEqual(len(evaluation.positive_probabilities[name]), len(y_validation))
            self.assertTrue(evaluation.predictions[name].index.equals(y_validation.index))
        for actual, expected in zip((X_train, X_validation, y_train, y_validation), originals, strict=True):
            if isinstance(actual, pd.DataFrame):
                pd.testing.assert_frame_equal(actual, expected)
            else:
                pd.testing.assert_series_equal(actual, expected)

    def test_validation_rows_cannot_enter_fit_inputs_through_api(self) -> None:
        parameters = tuple(inspect.signature(fit_and_evaluate_baselines).parameters)
        self.assertEqual(
            parameters,
            (
                "X_train_scaled",
                "X_validation_scaled",
                "X_train_unscaled",
                "X_validation_unscaled",
                "y_train",
                "y_validation",
            ),
        )
        self.assertFalse(any("test" in name.lower() for name in parameters))

    def test_every_model_fit_receives_train_rows_not_validation_rows(self) -> None:
        X_train, X_validation, y_train, y_validation = synthetic_processed_data()

        class TrackingClassifier:
            def fit(self, X: pd.DataFrame, y: pd.Series) -> "TrackingClassifier":
                self.fit_index_ = X.index.copy()
                self.classes_ = np.array(["No", "Yes"])
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                return np.full(len(X), "No")

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                return np.tile([0.7, 0.3], (len(X), 1))

        trackers = {name: TrackingClassifier() for name in MODEL_NAMES}
        with patch("fdm_rainfall.modeling.build_baseline_models", return_value=trackers):
            evaluation = fit_and_evaluate_baselines(
                X_train,
                X_validation,
                X_train,
                X_validation,
                y_train,
                y_validation,
            )

        for model in evaluation.fitted_models.values():
            self.assertTrue(model.fit_index_.equals(X_train.index))
            self.assertTrue(model.fit_index_.intersection(X_validation.index).empty)

    def test_no_test_prediction_or_metric_workflow_exists(self) -> None:
        source = inspect.getsource(fit_and_evaluate_baselines).lower()
        self.assertNotIn("x_test", source)
        self.assertNotIn("y_test", source)
        self.assertNotIn("test_score", source)

    def test_scaled_and_unscaled_representations_are_routed_by_model(self) -> None:
        X_train, X_validation, y_train, y_validation = synthetic_processed_data()
        X_train_scaled = X_train + 1_000.0
        X_validation_scaled = X_validation + 2_000.0
        X_train_unscaled = X_train + 3_000.0
        X_validation_unscaled = X_validation + 4_000.0

        class RoutingSpy:
            def __init__(
                self,
                expected_train: pd.DataFrame,
                expected_validation: pd.DataFrame,
            ) -> None:
                self.expected_train = expected_train
                self.expected_validation = expected_validation
                self.fit_called = False
                self.predict_called = False
                self.predict_proba_called = False

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "RoutingSpy":
                pd.testing.assert_frame_equal(X, self.expected_train)
                self.fit_called = True
                self.classes_ = np.array(["No", "Yes"])
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected_validation)
                self.predict_called = True
                return np.full(len(X), "No")

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected_validation)
                self.predict_proba_called = True
                return np.tile([0.7, 0.3], (len(X), 1))

        spies = {
            "Logistic Regression": RoutingSpy(X_train_scaled, X_validation_scaled),
            "Decision Tree": RoutingSpy(X_train_unscaled, X_validation_unscaled),
            "Random Forest": RoutingSpy(X_train_unscaled, X_validation_unscaled),
            "Gradient Boosting": RoutingSpy(X_train_unscaled, X_validation_unscaled),
        }
        with patch("fdm_rainfall.modeling.build_baseline_models", return_value=spies):
            fit_and_evaluate_baselines(
                X_train_scaled,
                X_validation_scaled,
                X_train_unscaled,
                X_validation_unscaled,
                y_train,
                y_validation,
            )

        for spy in spies.values():
            self.assertTrue(spy.fit_called)
            self.assertTrue(spy.predict_called)
            self.assertTrue(spy.predict_proba_called)

    def test_unaligned_validation_is_rejected(self) -> None:
        X_train, X_validation, y_train, y_validation = synthetic_processed_data()
        with self.assertRaisesRegex(ValueError, "indexes are not aligned"):
            fit_and_evaluate_baselines(
                X_train,
                X_validation,
                X_train,
                X_validation,
                y_train,
                y_validation.reset_index(drop=True),
            )


if __name__ == "__main__":
    unittest.main()
