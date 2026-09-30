"""Focused lightweight tests for T10 leakage-safe tuning."""

from __future__ import annotations

import inspect
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.features import RAW_NUMERICAL_PREDICTORS  # noqa: E402
from fdm_rainfall.modeling import METRIC_COLUMNS, MODEL_NAMES, POSITIVE_LABEL  # noqa: E402
from fdm_rainfall.tuning import (  # noqa: E402
    DateAwareFold,
    PreparedFold,
    TuningConfiguration,
    build_tuning_configurations,
    candidate_parameters,
    compare_baseline_and_tuned,
    date_aware_expanding_window_splits,
    fit_and_evaluate_tuned_models,
    prepare_cv_folds,
    prepare_engineered_train_validation,
    run_tuning_search,
    summarize_cv_results,
)


def synthetic_raw_frame(unique_dates: int = 16, rows_per_date: int = 2) -> pd.DataFrame:
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
    return frame


def prepared_pair(scale_numeric: bool, offset: float) -> PreparedFold:
    train_index = pd.Index(range(20))
    validation_index = pd.Index(range(100, 108))
    X_train = pd.DataFrame(
        np.full((20, 3), offset),
        index=train_index,
        columns=["a", "b", "c"],
    )
    X_validation = pd.DataFrame(
        np.full((8, 3), offset + 1),
        index=validation_index,
        columns=X_train.columns,
    )
    y_train = pd.Series(np.tile(["No", "Yes"], 10), index=train_index)
    y_validation = pd.Series(np.tile(["No", "Yes"], 4), index=validation_index)
    dates_train = pd.Series(pd.date_range("2020-01-01", periods=20), index=train_index)
    dates_validation = pd.Series(pd.date_range("2020-02-01", periods=8), index=validation_index)
    return PreparedFold(
        fold=0,
        scale_numeric=scale_numeric,
        feature_engineer=None,  # type: ignore[arg-type]
        preprocessor=None,  # type: ignore[arg-type]
        X_train=X_train,
        X_validation=X_validation,
        y_train=y_train,
        y_validation=y_validation,
        dates_train=dates_train,
        dates_validation=dates_validation,
    )


class TuningTests(unittest.TestCase):
    def test_date_aware_folds_are_strictly_chronological_and_keep_dates_whole(self) -> None:
        frame = synthetic_raw_frame()
        folds = date_aware_expanding_window_splits(frame["Date"], n_splits=3)

        self.assertEqual(len(folds), 3)
        for fold in folds:
            train_dates = set(frame.iloc[fold.train_positions]["Date"])
            validation_dates = set(frame.iloc[fold.validation_positions]["Date"])
            self.assertTrue(train_dates.isdisjoint(validation_dates))
            self.assertLess(max(train_dates), min(validation_dates))
            self.assertEqual(
                set(fold.train_positions).intersection(fold.validation_positions),
                set(),
            )
            for date, group in frame.groupby("Date"):
                positions = set(frame.index.get_indexer(group.index))
                self.assertFalse(
                    bool(positions.intersection(fold.train_positions))
                    and bool(positions.intersection(fold.validation_positions)),
                    msg=f"Date split across fold boundary: {date}",
                )

    def test_fold_preprocessing_is_fitted_only_on_fold_train_and_preserves_inputs(self) -> None:
        frame = synthetic_raw_frame()
        before = frame.copy(deep=True)
        folds = date_aware_expanding_window_splits(frame["Date"], n_splits=3)
        prepared = prepare_cv_folds(frame, folds, scale_numeric=True)

        for definition, result in zip(folds, prepared, strict=True):
            self.assertEqual(result.preprocessor.fit_row_count_, len(definition.train_positions))
            self.assertEqual(len(result.X_validation), len(definition.validation_positions))
            self.assertLess(result.dates_train.max(), result.dates_validation.min())
            self.assertEqual(result.X_train.shape[1], result.X_validation.shape[1])
            self.assertFalse(result.X_train.isna().any().any())
            self.assertFalse(result.X_validation.isna().any().any())
        pd.testing.assert_frame_equal(frame, before)

    def test_exactly_four_reproducible_tuning_configurations_and_spaces(self) -> None:
        first = build_tuning_configurations()
        second = build_tuning_configurations()
        self.assertEqual(tuple(first), MODEL_NAMES)
        self.assertEqual(first, second)
        self.assertTrue(first["Logistic Regression"].scale_numeric)
        for model_name in MODEL_NAMES[1:]:
            self.assertFalse(first[model_name].scale_numeric)

        self.assertEqual(set(first["Logistic Regression"].parameter_space), {"C", "class_weight"})
        self.assertTrue(
            {"max_depth", "min_samples_split", "min_samples_leaf", "class_weight"}.issubset(
                first["Decision Tree"].parameter_space
            )
        )
        self.assertTrue(
            {"n_estimators", "max_depth", "max_features", "class_weight"}.issubset(
                first["Random Forest"].parameter_space
            )
        )
        self.assertTrue(
            {"n_estimators", "learning_rate", "max_depth", "subsample"}.issubset(
                first["Gradient Boosting"].parameter_space
            )
        )

    def test_candidate_generation_is_deterministic_and_bounded(self) -> None:
        configurations = build_tuning_configurations()
        expected_counts = {
            "Logistic Regression": 8,
            "Decision Tree": 12,
            "Random Forest": 8,
            "Gradient Boosting": 6,
        }
        for model_name, configuration in configurations.items():
            first = candidate_parameters(configuration)
            second = candidate_parameters(configuration)
            self.assertEqual(first, second)
            self.assertEqual(len(first), expected_counts[model_name])

    def test_small_search_returns_fold_results_and_best_parameters(self) -> None:
        first_fold = replace(prepared_pair(scale_numeric=True, offset=10.0), fold=1)
        second_fold = replace(prepared_pair(scale_numeric=True, offset=20.0), fold=2)
        configuration = TuningConfiguration(
            model_name="Logistic Regression",
            scale_numeric=True,
            search_method="Exhaustive grid",
            parameter_space={"C": [0.1, 1.0], "class_weight": [None]},
        )

        result = run_tuning_search(configuration, [first_fold, second_fold])

        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(len(result.fold_results), 4)
        self.assertEqual(len(result.summary), 2)
        self.assertEqual(set(result.best_parameters), {"C", "class_weight"})
        self.assertTrue(np.isfinite(result.best_cv_pr_auc))

    def test_pr_auc_is_the_only_performance_ranking_metric(self) -> None:
        rows = []
        for candidate, roc_auc, f1 in ((1, 0.20, 0.10), (2, 0.99, 0.95)):
            for fold in (1, 2, 3):
                rows.append(
                    {
                        "Candidate": candidate,
                        "Parameters": f'{{"candidate":{candidate}}}',
                        "Fold": fold,
                        "Fit seconds": 0.01,
                        "PR-AUC": 0.50,
                        "ROC-AUC": roc_auc,
                        "F1 (Yes)": f1,
                        "Recall (Yes)": f1,
                        "Balanced Accuracy": roc_auc,
                    }
                )

        summary = summarize_cv_results(pd.DataFrame(rows))

        self.assertEqual(summary["Candidate"].tolist(), [1, 2])

    def test_yes_remains_the_positive_class(self) -> None:
        self.assertEqual(POSITIVE_LABEL, "Yes")

    def test_tuning_evaluation_api_has_no_test_arguments(self) -> None:
        for function in (fit_and_evaluate_tuned_models, prepare_cv_folds):
            parameters = inspect.signature(function).parameters
            self.assertFalse(any("test" in name.lower() for name in parameters))

    def test_outer_test_sentinel_never_enters_tuning_or_final_evaluation(self) -> None:
        frame = synthetic_raw_frame(unique_dates=16, rows_per_date=2)
        outer_train = frame.iloc[:24].copy()
        outer_validation = frame.iloc[24:28].copy()
        outer_test_sentinel = frame.iloc[28:].copy()
        test_before = outer_test_sentinel.copy(deep=True)
        forbidden_indices = set(outer_test_sentinel.index)

        folds = date_aware_expanding_window_splits(outer_train["Date"], n_splits=3)
        real_prepare = prepare_engineered_train_validation
        preparation_calls: list[tuple[set[int], set[int]]] = []

        def record_fold_preparation(
            train_frame: pd.DataFrame,
            validation_frame: pd.DataFrame,
            scale_numeric: bool,
            fold: int = 0,
        ) -> PreparedFold:
            train_indices = set(train_frame.index)
            validation_indices = set(validation_frame.index)
            self.assertTrue(train_indices.issubset(set(outer_train.index)))
            self.assertTrue(validation_indices.issubset(set(outer_train.index)))
            self.assertTrue(train_indices.isdisjoint(validation_indices))
            self.assertTrue(train_indices.isdisjoint(forbidden_indices))
            self.assertTrue(validation_indices.isdisjoint(forbidden_indices))
            preparation_calls.append((train_indices, validation_indices))
            return real_prepare(train_frame, validation_frame, scale_numeric, fold)

        with patch(
            "fdm_rainfall.tuning.prepare_engineered_train_validation",
            side_effect=record_fold_preparation,
        ):
            prepared_folds = prepare_cv_folds(outer_train, folds, scale_numeric=True)
        self.assertEqual(len(preparation_calls), 3)

        expected_folds = iter(prepared_folds)

        class FoldEvaluationSpy:
            def __init__(self, expected: PreparedFold) -> None:
                self.expected = expected
                self.classes_ = np.array(["No", "Yes"])

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "FoldEvaluationSpy":
                pd.testing.assert_frame_equal(X, self.expected.X_train)
                pd.testing.assert_series_equal(y, self.expected.y_train)
                self.assert_no_test_indices(X.index)
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                self.assert_no_test_indices(X.index)
                return self.expected.y_validation.to_numpy()

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                self.assert_no_test_indices(X.index)
                yes = (self.expected.y_validation.to_numpy() == "Yes").astype(float)
                return np.column_stack([1.0 - yes, yes])

            def assert_no_test_indices(self, index: pd.Index) -> None:
                if not set(index).isdisjoint(forbidden_indices):
                    raise AssertionError("Outer Test sentinel entered candidate evaluation")

        configuration = TuningConfiguration(
            model_name="Logistic Regression",
            scale_numeric=True,
            search_method="Exhaustive grid",
            parameter_space={"C": [0.1], "class_weight": [None]},
        )
        with patch(
            "fdm_rainfall.tuning.build_tuned_model",
            side_effect=lambda *_: FoldEvaluationSpy(next(expected_folds)),
        ):
            search = run_tuning_search(configuration, prepared_folds)
        self.assertEqual(len(search.fold_results), 3)

        scaled = real_prepare(outer_train, outer_validation, scale_numeric=True)
        unscaled = real_prepare(outer_train, outer_validation, scale_numeric=False)

        class FinalEvaluationSpy:
            def __init__(self, expected: PreparedFold) -> None:
                self.expected = expected
                self.classes_ = np.array(["No", "Yes"])

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "FinalEvaluationSpy":
                pd.testing.assert_frame_equal(X, self.expected.X_train)
                pd.testing.assert_series_equal(y, self.expected.y_train)
                self.assert_outer_train_only(X.index)
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                self.assert_outer_validation_only(X.index)
                return self.expected.y_validation.to_numpy()

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                self.assert_outer_validation_only(X.index)
                yes = (self.expected.y_validation.to_numpy() == "Yes").astype(float)
                return np.column_stack([1.0 - yes, yes])

            def assert_outer_train_only(self, index: pd.Index) -> None:
                if not set(index).issubset(set(outer_train.index)):
                    raise AssertionError("Final fit received rows outside outer Train")
                if not set(index).isdisjoint(forbidden_indices):
                    raise AssertionError("Outer Test sentinel entered final fit")

            def assert_outer_validation_only(self, index: pd.Index) -> None:
                if not set(index).issubset(set(outer_validation.index)):
                    raise AssertionError("Final evaluation received non-Validation rows")
                if not set(index).isdisjoint(forbidden_indices):
                    raise AssertionError("Outer Test sentinel entered final evaluation")

        def make_final_spy(model_name: str, parameters: dict[str, object]) -> FinalEvaluationSpy:
            expected = scaled if model_name == "Logistic Regression" else unscaled
            return FinalEvaluationSpy(expected)

        with patch("fdm_rainfall.tuning.build_tuned_model", side_effect=make_final_spy):
            evaluation = fit_and_evaluate_tuned_models(
                {name: {} for name in MODEL_NAMES},
                scaled,
                unscaled,
            )
        self.assertEqual(evaluation.comparison["Model"].tolist(), list(MODEL_NAMES))
        pd.testing.assert_frame_equal(outer_test_sentinel, test_before)

    def test_tuned_evaluation_routes_scaled_and_unscaled_data(self) -> None:
        scaled = prepared_pair(scale_numeric=True, offset=1_000.0)
        unscaled = prepared_pair(scale_numeric=False, offset=3_000.0)

        class RoutingSpy:
            def __init__(self, expected: PreparedFold) -> None:
                self.expected = expected
                self.classes_ = np.array(["No", "Yes"])

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "RoutingSpy":
                pd.testing.assert_frame_equal(X, self.expected.X_train)
                pd.testing.assert_series_equal(y, self.expected.y_train)
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                return np.full(len(X), "No")

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                pd.testing.assert_frame_equal(X, self.expected.X_validation)
                return np.tile([0.7, 0.3], (len(X), 1))

        def make_spy(model_name: str, parameters: dict[str, object]) -> RoutingSpy:
            expected = scaled if model_name == "Logistic Regression" else unscaled
            return RoutingSpy(expected)

        params = {name: {} for name in MODEL_NAMES}
        with patch("fdm_rainfall.tuning.build_tuned_model", side_effect=make_spy):
            result = fit_and_evaluate_tuned_models(params, scaled, unscaled)
        self.assertEqual(result.comparison["Model"].tolist(), list(MODEL_NAMES))

    def test_baseline_vs_tuned_changes_are_calculated_without_mutation(self) -> None:
        baseline = pd.DataFrame(
            [{"Model": name, **{metric: 0.50 for metric in METRIC_COLUMNS}} for name in MODEL_NAMES]
        )
        tuned = pd.DataFrame(
            [{"Model": name, **{metric: 0.60 for metric in METRIC_COLUMNS}} for name in MODEL_NAMES]
        )
        baseline_before = baseline.copy(deep=True)
        tuned_before = tuned.copy(deep=True)
        comparison = compare_baseline_and_tuned(baseline, tuned)

        self.assertEqual(comparison["Model"].tolist(), list(MODEL_NAMES))
        for metric in ("Accuracy", "Balanced Accuracy", "PR-AUC"):
            np.testing.assert_allclose(comparison[f"Change {metric}"], 0.10)
        pd.testing.assert_frame_equal(baseline, baseline_before)
        pd.testing.assert_frame_equal(tuned, tuned_before)


if __name__ == "__main__":
    unittest.main()
