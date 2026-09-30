"""Focused lightweight tests for T11 controlled feature optimization."""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.feature_optimization import (  # noqa: E402
    PreparedVariantFold,
    T10_TUNED_PARAMETERS,
    VARIANT_ORDER,
    apply_feature_variant,
    feature_variant_definitions,
    fit_selected_variants_on_validation,
    prepare_variant_train_validation,
    run_feature_experiment,
    select_feature_variants,
)
from fdm_rainfall.features import (  # noqa: E402
    RAW_NUMERICAL_PREDICTORS,
    WeatherFeatureEngineer,
)
from fdm_rainfall.modeling import MODEL_NAMES  # noqa: E402
from fdm_rainfall.tuning import date_aware_expanding_window_splits  # noqa: E402


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
    frame["Rainfall"] = np.resize([0.0, 1.0, 3.0, 8.0], rows)
    return frame


def raw_predictors(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop(columns="RainTomorrow")


def fake_prepared(variant: str, scaled: bool, fold: int) -> PreparedVariantFold:
    offset = 1_000.0 if scaled else 3_000.0
    train_index = pd.Index(range(fold * 100, fold * 100 + 8))
    validation_index = pd.Index(range(fold * 100 + 50, fold * 100 + 54))
    X_train = pd.DataFrame(offset, index=train_index, columns=["a", "b"])
    X_validation = pd.DataFrame(offset + 1, index=validation_index, columns=["a", "b"])
    y_train = pd.Series(np.tile(["No", "Yes"], 4), index=train_index)
    y_validation = pd.Series(np.tile(["No", "Yes"], 2), index=validation_index)
    return PreparedVariantFold(
        fold=fold,
        variant=variant,
        scale_numeric=scaled,
        preprocessor=None,  # type: ignore[arg-type]
        X_train=X_train,
        X_validation=X_validation,
        y_train=y_train,
        y_validation=y_validation,
        dates_train=pd.Series(pd.date_range("2020-01-01", periods=8), index=train_index),
        dates_validation=pd.Series(
            pd.date_range("2020-02-01", periods=4), index=validation_index
        ),
    )


class FeatureOptimizationTests(unittest.TestCase):
    def test_exactly_four_feature_variants_exist(self) -> None:
        self.assertEqual(tuple(feature_variant_definitions()), VARIANT_ORDER)
        self.assertEqual(len(VARIANT_ORDER), 4)

    def test_v0_reproduces_t08_default_without_mutation(self) -> None:
        source = raw_predictors(synthetic_raw_frame())
        before = source.copy(deep=True)
        expected = WeatherFeatureEngineer(output="default").fit_transform(source)
        actual = apply_feature_variant(source, "V0_DEFAULT")
        pd.testing.assert_frame_equal(actual, expected)
        pd.testing.assert_frame_equal(source, before)

    def test_v1_adds_year_and_keeps_cyclical_month(self) -> None:
        result = apply_feature_variant(
            raw_predictors(synthetic_raw_frame()), "V1_ADD_YEAR"
        )
        self.assertIn("Year", result)
        self.assertIn("Month_sin", result)
        self.assertIn("Month_cos", result)
        self.assertTrue((result["Year"] == 2020.0).all())

    def test_v2_replaces_rainfall_with_correct_log1p(self) -> None:
        source = raw_predictors(synthetic_raw_frame())
        before = source.copy(deep=True)
        result = apply_feature_variant(source, "V2_LOG_RAINFALL_REPLACE")
        self.assertIn("Rainfall_log1p", result)
        self.assertNotIn("Rainfall", result)
        np.testing.assert_allclose(result["Rainfall_log1p"], np.log1p(source["Rainfall"]))
        pd.testing.assert_frame_equal(source, before)

    def test_v3_contains_year_and_log_rainfall_but_not_raw_rainfall(self) -> None:
        result = apply_feature_variant(
            raw_predictors(synthetic_raw_frame()), "V3_YEAR_AND_LOG_RAINFALL"
        )
        self.assertIn("Year", result)
        self.assertIn("Rainfall_log1p", result)
        self.assertNotIn("Rainfall", result)

    def test_variants_reject_target_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "RainTomorrow must be separated"):
            apply_feature_variant(synthetic_raw_frame(), "V1_ADD_YEAR")

    def test_date_aware_cv_remains_chronological_and_keeps_dates_whole(self) -> None:
        frame = synthetic_raw_frame()
        folds = date_aware_expanding_window_splits(frame["Date"], n_splits=3)
        for fold in folds:
            train_dates = set(frame.iloc[fold.train_positions]["Date"])
            validation_dates = set(frame.iloc[fold.validation_positions]["Date"])
            self.assertTrue(train_dates.isdisjoint(validation_dates))
            self.assertLess(max(train_dates), min(validation_dates))
            self.assertFalse(
                set(fold.train_positions).intersection(fold.validation_positions)
            )

    def test_variant_preprocessing_fits_only_fold_train(self) -> None:
        frame = synthetic_raw_frame()
        train = frame.iloc[:24].copy()
        validation = frame.iloc[24:].copy()
        train_before = train.copy(deep=True)
        validation_before = validation.copy(deep=True)
        prepared = prepare_variant_train_validation(
            train,
            validation,
            "V3_YEAR_AND_LOG_RAINFALL",
            scale_numeric=True,
            fold=1,
        )
        self.assertEqual(prepared.preprocessor.fit_row_count_, len(train))
        self.assertTrue(prepared.preprocessor.fit_index_.equals(train.index))
        self.assertEqual(prepared.preprocessor.year_median_, 2020.0)
        self.assertEqual(prepared.X_train.shape[1], prepared.X_validation.shape[1])
        self.assertFalse(prepared.X_train.isna().any().any())
        self.assertFalse(prepared.X_validation.isna().any().any())
        pd.testing.assert_frame_equal(train, train_before)
        pd.testing.assert_frame_equal(validation, validation_before)

    def test_experiment_runs_48_fits_with_correct_scaling_routes(self) -> None:
        prepared = {
            variant: {
                "scaled": [fake_prepared(variant, True, fold) for fold in (1, 2, 3)],
                "unscaled": [fake_prepared(variant, False, fold) for fold in (1, 2, 3)],
            }
            for variant in VARIANT_ORDER
        }

        class RoutingSpy:
            def __init__(self, expected_offset: float) -> None:
                self.expected_offset = expected_offset
                self.classes_ = np.array(["No", "Yes"])

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "RoutingSpy":
                self.assert_offset(X, self.expected_offset)
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                self.assert_offset(X, self.expected_offset + 1)
                return np.tile(["No", "Yes"], len(X) // 2)

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                self.assert_offset(X, self.expected_offset + 1)
                return np.tile([[0.8, 0.2], [0.2, 0.8]], (len(X) // 2, 1))

            @staticmethod
            def assert_offset(X: pd.DataFrame, expected: float) -> None:
                if not np.allclose(X.to_numpy(), expected):
                    raise AssertionError("Incorrect scaling representation routed")

        def make_spy(model_name: str, parameters: dict[str, object]) -> RoutingSpy:
            self.assertEqual(parameters, T10_TUNED_PARAMETERS[model_name])
            return RoutingSpy(1_000.0 if model_name == "Logistic Regression" else 3_000.0)

        with patch(
            "fdm_rainfall.feature_optimization.build_tuned_model",
            side_effect=make_spy,
        ) as builder:
            result = run_feature_experiment(prepared)
        self.assertEqual(builder.call_count, 48)
        self.assertEqual(len(result.fold_results), 48)

    def test_representation_selection_uses_pr_auc_and_variant_order_only(self) -> None:
        rows = []
        for model_name in MODEL_NAMES:
            for position, variant in enumerate(VARIANT_ORDER):
                rows.append(
                    {
                        "Model": model_name,
                        "Variant": variant,
                        "CV PR-AUC mean": 0.75 if position < 2 else 0.70,
                        "CV PR-AUC std": 0.01,
                        "CV ROC-AUC mean": 0.10 if position == 0 else 0.99,
                        "CV F1 (Yes) mean": 0.10 if position == 0 else 0.99,
                    }
                )
        winners = select_feature_variants(pd.DataFrame(rows))
        self.assertTrue((winners["Selected feature variant"] == "V0_DEFAULT").all())
        self.assertTrue((winners["Tie-break required"] == "Yes").all())

    def test_outer_validation_metrics_cannot_change_selection(self) -> None:
        rows = []
        for model_name in MODEL_NAMES:
            for position, variant in enumerate(VARIANT_ORDER):
                rows.append(
                    {
                        "Model": model_name,
                        "Variant": variant,
                        "CV PR-AUC mean": 0.80 - position * 0.01,
                        "CV PR-AUC std": 0.01,
                        "Outer Validation PR-AUC": position,
                    }
                )
        first = select_feature_variants(pd.DataFrame(rows))
        for row in rows:
            row["Outer Validation PR-AUC"] *= -10_000
        second = select_feature_variants(pd.DataFrame(rows))
        pd.testing.assert_frame_equal(first, second)

    def test_outer_test_sentinel_cannot_enter_final_workflow(self) -> None:
        frame = synthetic_raw_frame()
        outer_train = frame.iloc[:24].copy()
        outer_validation = frame.iloc[24:28].copy()
        outer_test = frame.iloc[28:].copy()
        test_before = outer_test.copy(deep=True)
        forbidden = set(outer_test.index)
        winners = pd.DataFrame(
            {
                "Model": MODEL_NAMES,
                "Selected feature variant": VARIANT_ORDER,
            }
        )
        real_prepare = prepare_variant_train_validation

        def guarded_prepare(
            train_frame: pd.DataFrame,
            validation_frame: pd.DataFrame,
            variant: str,
            scale_numeric: bool,
            fold: int = 0,
        ) -> PreparedVariantFold:
            self.assertTrue(set(train_frame.index).isdisjoint(forbidden))
            self.assertTrue(set(validation_frame.index).isdisjoint(forbidden))
            self.assertTrue(set(train_frame.index).issubset(set(outer_train.index)))
            self.assertTrue(
                set(validation_frame.index).issubset(set(outer_validation.index))
            )
            return real_prepare(train_frame, validation_frame, variant, scale_numeric, fold)

        class FinalSpy:
            def __init__(self) -> None:
                self.classes_ = np.array(["No", "Yes"])

            def fit(self, X: pd.DataFrame, y: pd.Series) -> "FinalSpy":
                self.assert_safe(X)
                return self

            def predict(self, X: pd.DataFrame) -> np.ndarray:
                self.assert_safe(X)
                return np.tile(["No", "Yes"], len(X) // 2)

            def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
                self.assert_safe(X)
                return np.tile([[0.8, 0.2], [0.2, 0.8]], (len(X) // 2, 1))

            @staticmethod
            def assert_safe(X: pd.DataFrame) -> None:
                if not set(X.index).isdisjoint(forbidden):
                    raise AssertionError("Outer Test sentinel entered T11 workflow")

        with patch(
            "fdm_rainfall.feature_optimization.prepare_variant_train_validation",
            side_effect=guarded_prepare,
        ), patch(
            "fdm_rainfall.feature_optimization.build_tuned_model",
            side_effect=lambda *_: FinalSpy(),
        ):
            result = fit_selected_variants_on_validation(
                outer_train, outer_validation, winners
            )
        self.assertEqual(result.comparison["Model"].tolist(), list(MODEL_NAMES))
        pd.testing.assert_frame_equal(outer_test, test_before)
        self.assertNotIn("test", inspect.signature(fit_selected_variants_on_validation).parameters)


if __name__ == "__main__":
    unittest.main()
