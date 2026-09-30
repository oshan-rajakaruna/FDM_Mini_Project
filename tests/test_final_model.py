"""Behavioral tests for T12 final selection, isolation, and serialization."""

from __future__ import annotations

from dataclasses import replace
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.feature_optimization import T10_TUNED_PARAMETERS  # noqa: E402
from fdm_rainfall.features import RAW_NUMERICAL_PREDICTORS  # noqa: E402
from fdm_rainfall.final_model import (  # noqa: E402
    DEFAULT_THRESHOLD,
    FinalRainfallModelBundle,
    FrozenFinalConfiguration,
    PreparedFinalData,
    build_final_estimator,
    combine_train_validation_after_selection,
    fit_and_evaluate_final_model,
    final_execution_settings,
    frozen_model_hyperparameters,
    frozen_configuration_table,
    load_final_bundle,
    prepare_final_data,
    save_final_bundle,
    select_and_freeze_final_configuration,
)
from fdm_rainfall.modeling import MODEL_NAMES, calculate_binary_metrics  # noqa: E402
from fdm_rainfall.preprocessing import predictor_columns  # noqa: E402


METRICS = (
    "Accuracy",
    "Balanced Accuracy",
    "Precision (Yes)",
    "Recall (Yes)",
    "F1 (Yes)",
    "ROC-AUC",
    "PR-AUC",
)


def candidate_evidence(pr_auc: tuple[float, float, float, float] = (0.6, 0.5, 0.8, 0.7)) -> pd.DataFrame:
    variants = (
        "V2_LOG_RAINFALL_REPLACE",
        "V0_DEFAULT",
        "V0_DEFAULT",
        "V1_ADD_YEAR",
    )
    rows = []
    for position, (model, variant, score) in enumerate(
        zip(MODEL_NAMES, variants, pr_auc, strict=True)
    ):
        row = {
            "Model": model,
            "Selected feature variant": variant,
            "Accuracy": 0.99 - position * 0.1,
            "Balanced Accuracy": 0.2 + position * 0.1,
            "Precision (Yes)": 0.9 - position * 0.1,
            "Recall (Yes)": 0.1 + position * 0.1,
            "F1 (Yes)": 0.3 + position * 0.1,
            "ROC-AUC": 0.95 - position * 0.1,
            "PR-AUC": score,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def synthetic_raw_frame(unique_dates: int = 12, rows_per_date: int = 2) -> pd.DataFrame:
    rows = unique_dates * rows_per_date
    dates = pd.date_range("2020-01-01", periods=unique_dates, freq="D")
    frame = pd.DataFrame(
        {
            "Date": np.repeat(dates.strftime("%Y-%m-%d"), rows_per_date),
            "Location": np.tile(["A", "B"], rows // 2),
            "WindGustDir": np.tile(["N", "S"], rows // 2),
            "WindDir9am": np.tile(["E", "W"], rows // 2),
            "WindDir3pm": np.tile(["NE", "SW"], rows // 2),
            "RainToday": np.tile(["No", "Yes"], rows // 2),
            "RainTomorrow": np.tile(["No", "Yes"], rows // 2),
        },
        index=np.arange(100, 100 + rows),
    )
    for position, feature in enumerate(RAW_NUMERICAL_PREDICTORS):
        frame[feature] = np.arange(rows, dtype=float) + position + 1.0
    frame["Rainfall"] = np.resize([0.0, 1.0, 3.0, 8.0], rows)
    return frame


def frozen_configuration(model: str = "Random Forest", variant: str = "V0_DEFAULT") -> FrozenFinalConfiguration:
    return FrozenFinalConfiguration(
        model_family=model,
        hyperparameters=frozen_model_hyperparameters(model),
        feature_variant=variant,
        scale_numeric=model == "Logistic Regression",
        positive_class="Yes",
        negative_class="No",
        threshold=0.5,
        validation_metrics={metric: 0.7 for metric in METRICS},
        selection_rule="Validation PR-AUC only",
        tie_break_required=False,
        test_consulted=False,
    )


def toy_prepared() -> PreparedFinalData:
    development_index = pd.Index([10, 11, 12, 13, 14, 15])
    test_index = pd.Index([90, 91, 92, 93])
    return PreparedFinalData(
        preprocessor=None,  # type: ignore[arg-type]
        X_development=pd.DataFrame({"a": range(6), "b": range(10, 16)}, index=development_index),
        X_test=pd.DataFrame({"a": range(4), "b": range(20, 24)}, index=test_index),
        y_development=pd.Series(["No", "Yes", "No", "Yes", "No", "Yes"], index=development_index),
        y_test=pd.Series(["No", "Yes", "No", "Yes"], index=test_index),
        dates_development=pd.Series(pd.date_range("2020-01-01", periods=6), index=development_index),
        dates_test=pd.Series(pd.date_range("2020-02-01", periods=4), index=test_index),
    )


class EvaluationSpy:
    """Single selected estimator that records development/Test routing."""

    def __init__(self) -> None:
        self.classes_ = np.array(["No", "Yes"])
        self.fit_index: pd.Index | None = None
        self.probability_index: pd.Index | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "EvaluationSpy":
        self.fit_index = X.index.copy()
        self.fit_target = y.copy()
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        self.probability_index = X.index.copy()
        positive = np.array([0.4, 0.6, 0.8, 0.2])[: len(X)]
        return np.column_stack([1.0 - positive, positive])


class FinalModelTests(unittest.TestCase):
    def test_selection_uses_validation_pr_auc_only(self) -> None:
        evidence = candidate_evidence()
        evidence.loc[evidence["Model"] == "Decision Tree", [
            "Accuracy", "Balanced Accuracy", "Precision (Yes)", "Recall (Yes)",
            "F1 (Yes)", "ROC-AUC",
        ]] = 1.0
        result = select_and_freeze_final_configuration(evidence)
        self.assertEqual(result.configuration.model_family, "Random Forest")

    def test_test_metrics_are_rejected_from_selection(self) -> None:
        evidence = candidate_evidence().assign(**{"Test PR-AUC": [1.0, 0.0, 0.0, 0.0]})
        with self.assertRaisesRegex(ValueError, "Validation evidence only"):
            select_and_freeze_final_configuration(evidence)

    def test_correct_synthetic_winner_is_derived(self) -> None:
        result = select_and_freeze_final_configuration(candidate_evidence())
        self.assertEqual(result.candidates.iloc[0]["Model"], "Random Forest")
        self.assertEqual(result.candidates.iloc[0]["Selected final model"], "Yes")

    def test_exact_pr_auc_tie_uses_neutral_model_order(self) -> None:
        result = select_and_freeze_final_configuration(
            candidate_evidence((0.8, 0.8, 0.8, 0.8))
        )
        self.assertEqual(result.configuration.model_family, "Logistic Regression")
        self.assertTrue(result.configuration.tie_break_required)

    def test_t10_hyperparameters_are_frozen_exactly(self) -> None:
        configuration = select_and_freeze_final_configuration(candidate_evidence()).configuration
        expected = {
            **T10_TUNED_PARAMETERS["Random Forest"],
            "random_state": 42,
        }
        self.assertEqual(configuration.hyperparameters, expected)
        self.assertNotIn("n_jobs", configuration.hyperparameters)
        table = frozen_configuration_table(configuration)
        self.assertEqual(json.loads(table.iloc[0]["Exact hyperparameters"]), expected)
        self.assertEqual(
            table.iloc[0]["Estimator execution setting"],
            "n_jobs=1 (execution-only portability setting)",
        )
        self.assertEqual(final_execution_settings("Random Forest"), {"n_jobs": 1})
        estimator = build_final_estimator(configuration)
        for name, value in expected.items():
            self.assertEqual(estimator.get_params()[name], value)
        self.assertEqual(estimator.get_params()["n_jobs"], 1)

    def test_t11_selected_representation_is_preserved(self) -> None:
        result = select_and_freeze_final_configuration(candidate_evidence())
        self.assertEqual(result.configuration.feature_variant, "V0_DEFAULT")

    def test_train_validation_combination_requires_frozen_selection(self) -> None:
        frame = synthetic_raw_frame()
        train, validation = frame.iloc[:12], frame.iloc[12:20]
        combined = combine_train_validation_after_selection(
            train, validation, frozen_configuration()
        )
        self.assertEqual(len(combined), len(train) + len(validation))
        self.assertTrue(combined.index.equals(pd.Index([*train.index, *validation.index])))

    def test_test_rows_are_excluded_from_final_fit(self) -> None:
        prepared = toy_prepared()
        spy = EvaluationSpy()
        with patch("fdm_rainfall.final_model.build_final_estimator", return_value=spy):
            fit_and_evaluate_final_model(prepared, frozen_configuration())
        self.assertTrue(spy.fit_index.equals(prepared.X_development.index))
        self.assertTrue(set(spy.fit_index).isdisjoint(prepared.X_test.index))

    def test_final_preprocessor_fits_only_development_indices(self) -> None:
        frame = synthetic_raw_frame()
        development, test = frame.iloc[:16].copy(), frame.iloc[16:].copy()
        prepared = prepare_final_data(development, test, frozen_configuration())
        self.assertTrue(prepared.preprocessor.fit_index_.equals(development.index))
        self.assertEqual(prepared.preprocessor.fit_row_count_, len(development))

    def test_test_is_transform_only_for_preprocessing_statistics(self) -> None:
        frame = synthetic_raw_frame()
        development, test = frame.iloc[:16].copy(), frame.iloc[16:].copy()
        test.loc[:, "MinTemp"] = 1_000_000.0
        prepared = prepare_final_data(development, test, frozen_configuration())
        expected = float(development["MinTemp"].median())
        self.assertEqual(prepared.preprocessor.base_preprocessor_.numeric_medians_["MinTemp"], expected)

    def test_exactly_one_selected_model_is_built_for_test(self) -> None:
        spy = EvaluationSpy()
        with patch("fdm_rainfall.final_model.build_final_estimator", return_value=spy) as builder:
            fit_and_evaluate_final_model(toy_prepared(), frozen_configuration())
        builder.assert_called_once()
        self.assertEqual(builder.call_args.args[0].model_family, "Random Forest")

    def test_non_selected_estimators_never_receive_test(self) -> None:
        prepared = toy_prepared()
        spy = EvaluationSpy()
        built_families: list[str] = []

        def build_selected(configuration: FrozenFinalConfiguration) -> EvaluationSpy:
            built_families.append(configuration.model_family)
            return spy

        with patch(
            "fdm_rainfall.final_model.build_final_estimator",
            side_effect=build_selected,
        ):
            fit_and_evaluate_final_model(prepared, frozen_configuration())
        self.assertEqual(built_families, ["Random Forest"])
        self.assertTrue(spy.probability_index.equals(prepared.X_test.index))

    def test_yes_is_frozen_positive_class(self) -> None:
        configuration = select_and_freeze_final_configuration(candidate_evidence()).configuration
        self.assertEqual(configuration.positive_class, "Yes")
        table = frozen_configuration_table(configuration)
        self.assertEqual(table.iloc[0]["Positive class"], "Yes")

    def test_threshold_remains_point_five(self) -> None:
        spy = EvaluationSpy()
        with patch("fdm_rainfall.final_model.build_final_estimator", return_value=spy):
            result = fit_and_evaluate_final_model(toy_prepared(), frozen_configuration())
        self.assertEqual(DEFAULT_THRESHOLD, 0.5)
        self.assertEqual(result.predictions.tolist(), ["No", "Yes", "Yes", "No"])

    def test_confusion_order_is_tn_fp_fn_tp(self) -> None:
        spy = EvaluationSpy()
        with patch("fdm_rainfall.final_model.build_final_estimator", return_value=spy):
            result = fit_and_evaluate_final_model(toy_prepared(), frozen_configuration())
        row = result.comparison.iloc[0]
        self.assertEqual([row["TN"], row["FP"], row["FN"], row["TP"]], [1, 1, 1, 1])

    def test_metric_calculation_matches_known_example(self) -> None:
        metrics = calculate_binary_metrics(
            np.array(["No", "Yes", "No", "Yes"]),
            np.array(["No", "Yes", "Yes", "No"]),
            np.array([0.4, 0.6, 0.8, 0.2]),
        )
        for metric in ("Accuracy", "Balanced Accuracy", "Precision (Yes)", "Recall (Yes)", "F1 (Yes)"):
            self.assertEqual(metrics[metric], 0.5)

    def _round_trip(self) -> tuple[FinalRainfallModelBundle, FinalRainfallModelBundle, pd.DataFrame]:
        X = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0], "b": [1.0, 1.0, 0.0, 0.0]})
        y = pd.Series(["No", "No", "Yes", "Yes"])
        estimator = DecisionTreeClassifier(random_state=42).fit(X, y)
        bundle = FinalRainfallModelBundle(
            estimator=estimator,
            preprocessor=None,  # type: ignore[arg-type]
            configuration=frozen_configuration("Decision Tree"),
            processed_feature_names=("a", "b"),
            expected_raw_columns=("Date", *predictor_columns()),
            metadata={"model_version": "test"},
        )
        path = PROJECT_ROOT / "tests" / ".t12_serialization_test.joblib"
        self.addCleanup(path.unlink, missing_ok=True)
        save_final_bundle(bundle, path)
        return bundle, load_final_bundle(path), X

    def test_serialized_bundle_loads_successfully(self) -> None:
        _, loaded, _ = self._round_trip()
        self.assertIsInstance(loaded, FinalRainfallModelBundle)

    def test_loaded_predictions_match_original(self) -> None:
        original, loaded, X = self._round_trip()
        np.testing.assert_array_equal(original.estimator.predict(X), loaded.estimator.predict(X))

    def test_loaded_probabilities_match_within_tolerance(self) -> None:
        original, loaded, X = self._round_trip()
        np.testing.assert_allclose(
            original.estimator.predict_proba(X), loaded.estimator.predict_proba(X)
        )

    def test_input_datasets_are_not_mutated(self) -> None:
        frame = synthetic_raw_frame()
        development, test = frame.iloc[:16].copy(), frame.iloc[16:].copy()
        development_before, test_before = development.copy(deep=True), test.copy(deep=True)
        prepare_final_data(development, test, frozen_configuration())
        pd.testing.assert_frame_equal(development, development_before)
        pd.testing.assert_frame_equal(test, test_before)

    def test_behavioral_selection_and_test_sentinel_boundary(self) -> None:
        selection = select_and_freeze_final_configuration(candidate_evidence())
        self.assertFalse(selection.configuration.test_consulted)
        prepared = toy_prepared()
        test_before = prepared.y_test.copy(deep=True)
        spy = EvaluationSpy()
        with patch("fdm_rainfall.final_model.build_final_estimator", return_value=spy) as builder:
            result = fit_and_evaluate_final_model(prepared, selection.configuration)
        builder.assert_called_once_with(selection.configuration)
        self.assertTrue(set(spy.fit_index).isdisjoint(prepared.X_test.index))
        self.assertTrue(spy.probability_index.equals(prepared.X_test.index))
        pd.testing.assert_series_equal(prepared.y_test, test_before)
        self.assertEqual(result.bundle.configuration, selection.configuration)
        self.assertEqual(result.bundle.metadata["hyperparameters"]["random_state"], 42)
        self.assertNotIn("n_jobs", result.bundle.metadata["hyperparameters"])
        self.assertEqual(result.bundle.metadata["execution_settings"], {"n_jobs": 1})

    def test_non_default_threshold_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "default threshold"):
            fit_and_evaluate_final_model(
                toy_prepared(), replace(frozen_configuration(), threshold=0.4)
            )


if __name__ == "__main__":
    unittest.main()
