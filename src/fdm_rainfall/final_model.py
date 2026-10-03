"""Dynamic final selection, persistence, and one-time holdout evaluation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

from fdm_rainfall.feature_optimization import (
    COMPARISON_METRICS,
    T10_TUNED_PARAMETERS,
    VARIANT_ORDER,
    FeatureVariantPreprocessor,
    apply_feature_variant,
)
from fdm_rainfall.modeling import (
    MODEL_NAMES,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    RANDOM_STATE,
    calculate_binary_metrics,
    positive_class_probability,
)
from fdm_rainfall.preprocessing import (
    DATE_COLUMN,
    predictor_columns,
    separate_supervised_components,
)
from fdm_rainfall.tuning import build_tuned_model


DEFAULT_THRESHOLD = 0.5
FINAL_SELECTION_RULE = (
    "Highest full-precision T11 Validation PR-AUC; exact ties use the fixed "
    "candidate order Logistic Regression, Decision Tree, Random Forest, "
    "Gradient Boosting"
)
FINAL_RF_N_JOBS = 1
MODEL_ARTIFACT_FILENAMES = {
    "Logistic Regression": "logistic_regression.joblib",
    "Decision Tree": "decision_tree.joblib",
    "Random Forest": "random_forest.joblib",
    "Gradient Boosting": "gradient_boosting.joblib",
}
ARTIFACT_ROLES = frozenset({"final", "comparison"})


def frozen_model_hyperparameters(model_family: str) -> dict[str, Any]:
    """Return the complete reproducible model record frozen before Test."""

    parameters = deepcopy(T10_TUNED_PARAMETERS[model_family])
    if model_family == "Logistic Regression":
        parameters["max_iter"] = 1000
    parameters["random_state"] = RANDOM_STATE
    return parameters


def final_execution_settings(model_family: str) -> dict[str, Any]:
    """Return portability settings kept separate from tuned hyperparameters."""

    return {"n_jobs": FINAL_RF_N_JOBS} if model_family == "Random Forest" else {}


@dataclass(frozen=True)
class FrozenFinalConfiguration:
    """Final modeling decisions fixed before any Test prediction is generated."""

    model_family: str
    hyperparameters: dict[str, Any]
    feature_variant: str
    scale_numeric: bool
    positive_class: str
    negative_class: str
    threshold: float
    validation_metrics: dict[str, float]
    selection_rule: str
    tie_break_required: bool
    test_consulted: bool = False


@dataclass(frozen=True)
class FinalSelection:
    """Ranked pre-Test evidence and its frozen winning configuration."""

    candidates: pd.DataFrame
    configuration: FrozenFinalConfiguration


@dataclass(frozen=True)
class PreparedFinalData:
    """Train+Validation-fitted preprocessing and transform-only Test matrices."""

    preprocessor: FeatureVariantPreprocessor
    X_development: pd.DataFrame
    X_test: pd.DataFrame
    y_development: pd.Series
    y_test: pd.Series
    dates_development: pd.Series
    dates_test: pd.Series


@dataclass
class FinalRainfallModelBundle:
    """Deployable estimator, preprocessing state, and frozen inference metadata."""

    estimator: ClassifierMixin
    preprocessor: FeatureVariantPreprocessor
    configuration: FrozenFinalConfiguration
    processed_feature_names: tuple[str, ...]
    expected_raw_columns: tuple[str, ...]
    metadata: dict[str, Any]

    def _transform(self, raw_predictors: pd.DataFrame) -> pd.DataFrame:
        """Apply the frozen representation and fitted preprocessing state."""

        expected = set(self.expected_raw_columns)
        missing = sorted(expected.difference(raw_predictors.columns))
        extra = sorted(set(raw_predictors.columns).difference(expected))
        if missing or extra:
            raise ValueError(
                f"Raw inference schema mismatch; missing={missing}, extra={extra}"
            )
        source = raw_predictors.loc[:, self.expected_raw_columns].copy(deep=True)
        engineered = apply_feature_variant(source, self.configuration.feature_variant)
        transformed = self.preprocessor.transform(engineered)
        if tuple(transformed.columns) != self.processed_feature_names:
            raise RuntimeError("Processed inference schema differs from frozen schema")
        return transformed

    def predict_positive_probability(self, raw_predictors: pd.DataFrame) -> np.ndarray:
        """Return RainTomorrow=Yes probabilities from the frozen bundle."""

        return positive_class_probability(self.estimator, self._transform(raw_predictors))

    def predict(self, raw_predictors: pd.DataFrame) -> np.ndarray:
        """Classify with the frozen default probability threshold."""

        probabilities = self.predict_positive_probability(raw_predictors)
        return np.where(
            probabilities >= self.configuration.threshold,
            self.configuration.positive_class,
            self.configuration.negative_class,
        )


@dataclass(frozen=True)
class FinalTestEvaluation:
    """Outputs from evaluating exactly one frozen model on Test."""

    bundle: FinalRainfallModelBundle
    comparison: pd.DataFrame
    predictions: pd.Series
    positive_probabilities: pd.Series


def _reject_test_selection_columns(frame: pd.DataFrame) -> None:
    contaminated = [column for column in frame.columns if "test" in str(column).lower()]
    if contaminated:
        raise ValueError(
            "Final selection accepts Validation evidence only; remove Test columns: "
            + ", ".join(map(str, contaminated))
        )


def select_and_freeze_final_configuration(
    validation_candidates: pd.DataFrame,
) -> FinalSelection:
    """Select strictly by T11 Validation PR-AUC and freeze all decisions."""

    _reject_test_selection_columns(validation_candidates)
    required = {"Model", "Selected feature variant", *COMPARISON_METRICS}
    missing = sorted(required.difference(validation_candidates.columns))
    if missing:
        raise ValueError(f"Validation candidate columns are missing: {', '.join(missing)}")
    if len(validation_candidates) != len(MODEL_NAMES):
        raise ValueError("Final selection requires exactly four T11 candidates")
    if validation_candidates["Model"].duplicated().any():
        raise ValueError("Each model family must appear exactly once")
    if set(validation_candidates["Model"]) != set(MODEL_NAMES):
        raise ValueError("Final selection candidates must be the four T09 model families")
    if not set(validation_candidates["Selected feature variant"]).issubset(
        set(VARIANT_ORDER)
    ):
        raise ValueError("Candidate contains an unknown T11 feature variant")
    pr_auc = pd.to_numeric(validation_candidates["PR-AUC"], errors="coerce")
    if pr_auc.isna().any() or not np.isfinite(pr_auc).all():
        raise ValueError("Validation PR-AUC values must be finite")

    order = {name: position for position, name in enumerate(MODEL_NAMES)}
    ranked = validation_candidates.copy(deep=True)
    ranked["_candidate_order"] = ranked["Model"].map(order)
    ranked = ranked.sort_values(
        ["PR-AUC", "_candidate_order"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked["Validation PR-AUC rank"] = np.arange(1, len(ranked) + 1)
    ranked["Selected final model"] = ["Yes", *(["No"] * (len(ranked) - 1))]
    winner = ranked.iloc[0]
    exact_ties = int((ranked["PR-AUC"] == winner["PR-AUC"]).sum())
    validation_metrics = {
        metric: float(winner[metric]) for metric in COMPARISON_METRICS
    }
    configuration = FrozenFinalConfiguration(
        model_family=str(winner["Model"]),
        hyperparameters=frozen_model_hyperparameters(str(winner["Model"])),
        feature_variant=str(winner["Selected feature variant"]),
        scale_numeric=str(winner["Model"]) == "Logistic Regression",
        positive_class=POSITIVE_LABEL,
        negative_class=NEGATIVE_LABEL,
        threshold=DEFAULT_THRESHOLD,
        validation_metrics=validation_metrics,
        selection_rule=FINAL_SELECTION_RULE,
        tie_break_required=exact_ties > 1,
        test_consulted=False,
    )
    return FinalSelection(
        candidates=ranked.drop(columns="_candidate_order"),
        configuration=configuration,
    )


def freeze_all_candidate_configurations(
    validation_candidates: pd.DataFrame,
) -> tuple[FinalSelection, dict[str, FrozenFinalConfiguration]]:
    """Freeze all four candidates while selecting exactly one by Validation PR-AUC."""

    selection = select_and_freeze_final_configuration(validation_candidates)
    indexed = validation_candidates.set_index("Model", drop=False)
    configurations: dict[str, FrozenFinalConfiguration] = {}
    for model_family in MODEL_NAMES:
        if model_family == selection.configuration.model_family:
            configurations[model_family] = selection.configuration
            continue
        row = indexed.loc[model_family]
        configurations[model_family] = FrozenFinalConfiguration(
            model_family=model_family,
            hyperparameters=frozen_model_hyperparameters(model_family),
            feature_variant=str(row["Selected feature variant"]),
            scale_numeric=model_family == "Logistic Regression",
            positive_class=POSITIVE_LABEL,
            negative_class=NEGATIVE_LABEL,
            threshold=DEFAULT_THRESHOLD,
            validation_metrics={
                metric: float(row[metric]) for metric in COMPARISON_METRICS
            },
            selection_rule=FINAL_SELECTION_RULE,
            tie_break_required=False,
            test_consulted=False,
        )
    return selection, configurations


def frozen_configuration_table(
    configuration: FrozenFinalConfiguration,
) -> pd.DataFrame:
    """Return the frozen pre-Test decisions as one machine-readable row."""

    row: dict[str, object] = {
        "Selected model family": configuration.model_family,
        "Exact hyperparameters": json.dumps(
            configuration.hyperparameters, sort_keys=True, separators=(",", ":")
        ),
        "Selected feature variant": configuration.feature_variant,
        "Scaling route": "scaled" if configuration.scale_numeric else "unscaled",
        "Positive class": configuration.positive_class,
        "Negative class": configuration.negative_class,
        "Classification threshold": configuration.threshold,
        "Selection rule": configuration.selection_rule,
        "Exact tie-break required": "Yes" if configuration.tie_break_required else "No",
        "Test consulted during selection": "Yes" if configuration.test_consulted else "No",
        "Configuration frozen before Test access": "Yes",
        "Estimator execution setting": (
            f"n_jobs={FINAL_RF_N_JOBS} (execution-only portability setting)"
            if configuration.model_family == "Random Forest"
            else "default single-process execution"
        ),
    }
    row.update(
        {
            f"Selection Validation {metric}": value
            for metric, value in configuration.validation_metrics.items()
        }
    )
    return pd.DataFrame([row])


def combine_train_validation_after_selection(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    configuration: FrozenFinalConfiguration,
) -> pd.DataFrame:
    """Combine development subsets only after a frozen selection exists."""

    if configuration.test_consulted:
        raise ValueError("A Test-informed configuration cannot be used")
    if set(train.index).intersection(validation.index):
        raise ValueError("Train and Validation source indices overlap")
    train_dates = pd.to_datetime(train[DATE_COLUMN], errors="coerce")
    validation_dates = pd.to_datetime(validation[DATE_COLUMN], errors="coerce")
    if train_dates.isna().any() or validation_dates.isna().any():
        raise ValueError("Train and Validation dates must be complete")
    if train_dates.max() >= validation_dates.min():
        raise ValueError("Train must end before Validation begins")
    combined = pd.concat(
        [train.copy(deep=True), validation.copy(deep=True)], axis=0
    ).sort_values(DATE_COLUMN, kind="mergesort")
    if len(combined) != len(train) + len(validation):
        raise RuntimeError("Train+Validation row reconciliation failed")
    return combined


def prepare_final_data(
    development: pd.DataFrame,
    test: pd.DataFrame,
    configuration: FrozenFinalConfiguration,
) -> PreparedFinalData:
    """Fit final preprocessing on Train+Validation and transform Test only."""

    if configuration.test_consulted:
        raise ValueError("A Test-informed configuration cannot be used")
    if set(development.index).intersection(test.index):
        raise ValueError("Development and Test source indices overlap")
    development_parts = separate_supervised_components(development)
    test_parts = separate_supervised_components(test)
    if pd.to_datetime(development_parts.dates).max() >= pd.to_datetime(
        test_parts.dates
    ).min():
        raise ValueError("Development must end before Test begins")
    raw_development = pd.concat(
        [development_parts.dates.rename(DATE_COLUMN), development_parts.X], axis=1
    )
    raw_test = pd.concat([test_parts.dates.rename(DATE_COLUMN), test_parts.X], axis=1)
    engineered_development = apply_feature_variant(
        raw_development, configuration.feature_variant
    )
    engineered_test = apply_feature_variant(raw_test, configuration.feature_variant)
    preprocessor = FeatureVariantPreprocessor(
        configuration.feature_variant, configuration.scale_numeric
    )
    X_development = preprocessor.fit_transform(engineered_development)
    X_test = preprocessor.transform(engineered_test)
    if list(X_development.columns) != list(X_test.columns):
        raise RuntimeError("Final development and Test schemas differ")
    return PreparedFinalData(
        preprocessor=preprocessor,
        X_development=X_development,
        X_test=X_test,
        y_development=development_parts.y,
        y_test=test_parts.y,
        dates_development=development_parts.dates,
        dates_test=test_parts.dates,
    )


def build_final_estimator(
    configuration: FrozenFinalConfiguration,
) -> ClassifierMixin:
    """Instantiate the selected T10 model without tuning or alternatives."""

    expected = frozen_model_hyperparameters(configuration.model_family)
    if configuration.hyperparameters != expected:
        raise ValueError("Frozen hyperparameters differ from the T10 winner")
    estimator = build_tuned_model(
        configuration.model_family, deepcopy(configuration.hyperparameters)
    )
    if configuration.model_family == "Random Forest":
        estimator.set_params(**final_execution_settings(configuration.model_family))
    return estimator


def fit_development_bundle(
    development: pd.DataFrame,
    configuration: FrozenFinalConfiguration,
    artifact_role: str,
) -> FinalRainfallModelBundle:
    """Fit one frozen candidate on Train+Validation without accepting Test data."""

    if artifact_role not in ARTIFACT_ROLES:
        raise ValueError(f"Unknown artifact role: {artifact_role}")
    if configuration.test_consulted:
        raise ValueError("A Test-informed configuration cannot be persisted")
    development_before = development.copy(deep=True)
    parts = separate_supervised_components(development)
    raw_development = pd.concat(
        [parts.dates.rename(DATE_COLUMN), parts.X], axis=1
    )
    engineered = apply_feature_variant(
        raw_development, configuration.feature_variant
    )
    preprocessor = FeatureVariantPreprocessor(
        configuration.feature_variant, configuration.scale_numeric
    )
    X_development = preprocessor.fit_transform(engineered)
    estimator = build_final_estimator(configuration)
    estimator.fit(X_development, parts.y)
    pd.testing.assert_frame_equal(development, development_before)

    metadata = {
        "project": "IT3051 FDM Mini Project",
        "model_version": "T12-persisted-v2",
        "model_id": MODEL_ARTIFACT_FILENAMES[configuration.model_family].removesuffix(
            ".joblib"
        ),
        "model_family": configuration.model_family,
        "artifact_role": artifact_role,
        "hyperparameters": deepcopy(configuration.hyperparameters),
        "execution_settings": final_execution_settings(configuration.model_family),
        "feature_variant": configuration.feature_variant,
        "scale_numeric": configuration.scale_numeric,
        "scaling_mode": "scaled" if configuration.scale_numeric else "unscaled",
        "positive_class": configuration.positive_class,
        "negative_class": configuration.negative_class,
        "threshold": configuration.threshold,
        "selection_rule": configuration.selection_rule,
        "test_consulted_during_selection": configuration.test_consulted,
        "development_first_date": pd.to_datetime(parts.dates)
        .min()
        .date()
        .isoformat(),
        "development_last_date": pd.to_datetime(parts.dates)
        .max()
        .date()
        .isoformat(),
        "development_rows": len(X_development),
        "processed_feature_count": X_development.shape[1],
        "expected_raw_columns": [DATE_COLUMN, *predictor_columns()],
        "contains_raw_rows": False,
        "contains_test_labels": False,
        "contains_test_predictions": False,
        "contains_test_probabilities": False,
        "contains_test_metrics": False,
        "test_used_for_artifact_fitting": False,
        "post_test_model_changes": False,
    }
    return FinalRainfallModelBundle(
        estimator=estimator,
        preprocessor=preprocessor,
        configuration=configuration,
        processed_feature_names=tuple(X_development.columns),
        expected_raw_columns=(DATE_COLUMN, *predictor_columns()),
        metadata=metadata,
    )


def evaluate_fitted_final_bundle(
    bundle: FinalRainfallModelBundle,
    test: pd.DataFrame,
) -> FinalTestEvaluation:
    """Evaluate only the already-selected, already-fitted final bundle on Test."""

    if bundle.metadata.get("artifact_role") != "final":
        raise ValueError("Only the selected final bundle may receive Test data")
    if bundle.configuration.test_consulted:
        raise ValueError("A Test-informed configuration cannot be evaluated")
    test_before = test.copy(deep=True)
    parts = separate_supervised_components(test)
    test_dates = pd.to_datetime(parts.dates, errors="coerce")
    if test_dates.isna().any():
        raise ValueError("Test dates must be complete")
    development_last = pd.Timestamp(bundle.metadata["development_last_date"])
    if development_last >= test_dates.min():
        raise ValueError("Development must end before Test begins")
    if set(bundle.preprocessor.fit_index_).intersection(test.index):
        raise ValueError("Test rows cannot appear in fitted preprocessing state")

    raw_test = pd.concat([parts.dates.rename(DATE_COLUMN), parts.X], axis=1)
    probabilities_array = bundle.predict_positive_probability(raw_test)
    predictions_array = np.where(
        probabilities_array >= bundle.configuration.threshold,
        bundle.configuration.positive_class,
        bundle.configuration.negative_class,
    )
    probabilities = pd.Series(
        probabilities_array,
        index=parts.y.index,
        name=f"{bundle.configuration.model_family} positive probability",
    )
    predictions = pd.Series(
        predictions_array,
        index=parts.y.index,
        name=f"{bundle.configuration.model_family} prediction",
    )
    metrics = calculate_binary_metrics(parts.y, predictions, probabilities)
    row: dict[str, object] = {
        "Model": bundle.configuration.model_family,
        "Selected feature variant": bundle.configuration.feature_variant,
        "Processed feature count": len(bundle.processed_feature_names),
        "Development rows": bundle.metadata["development_rows"],
        "Test rows": len(test),
        "Threshold": bundle.configuration.threshold,
    }
    row.update(metrics)
    metadata = deepcopy(bundle.metadata)
    metadata.update(
        {
            "test_first_date": test_dates.min().date().isoformat(),
            "test_last_date": test_dates.max().date().isoformat(),
            "test_rows_evaluated": len(test),
            "contains_test_labels": False,
            "contains_test_predictions": False,
            "contains_test_probabilities": False,
            "contains_test_metrics": False,
            "post_test_model_changes": False,
        }
    )
    evaluated_bundle = FinalRainfallModelBundle(
        estimator=bundle.estimator,
        preprocessor=bundle.preprocessor,
        configuration=bundle.configuration,
        processed_feature_names=bundle.processed_feature_names,
        expected_raw_columns=bundle.expected_raw_columns,
        metadata=metadata,
    )
    pd.testing.assert_frame_equal(test, test_before)
    return FinalTestEvaluation(
        bundle=evaluated_bundle,
        comparison=pd.DataFrame([row]),
        predictions=predictions,
        positive_probabilities=probabilities,
    )


def model_artifact_paths(
    selected_model_family: str,
    models_directory: str | Path,
) -> dict[str, Path]:
    """Route the Validation winner to the final path and all others to comparison."""

    if selected_model_family not in MODEL_NAMES:
        raise ValueError(f"Unknown selected model: {selected_model_family}")
    root = Path(models_directory)
    return {
        model_family: (
            root / "final_rainfall_model.joblib"
            if model_family == selected_model_family
            else root / "comparison" / MODEL_ARTIFACT_FILENAMES[model_family]
        )
        for model_family in MODEL_NAMES
    }


def save_ranked_model_bundles(
    bundles: Mapping[str, FinalRainfallModelBundle],
    selected_model_family: str,
    models_directory: str | Path,
) -> dict[str, Path]:
    """Persist one dynamic winner and exactly three comparison bundles."""

    if set(bundles) != set(MODEL_NAMES):
        raise ValueError("Exactly the four established model bundles are required")
    paths = model_artifact_paths(selected_model_family, models_directory)
    comparison_directory = Path(models_directory) / "comparison"
    comparison_directory.mkdir(parents=True, exist_ok=True)
    for filename in MODEL_ARTIFACT_FILENAMES.values():
        (comparison_directory / filename).unlink(missing_ok=True)

    for model_family in MODEL_NAMES:
        bundle = bundles[model_family]
        expected_role = "final" if model_family == selected_model_family else "comparison"
        if bundle.configuration.model_family != model_family:
            raise ValueError("Bundle key and configured model family differ")
        if bundle.metadata.get("artifact_role") != expected_role:
            raise ValueError(
                f"{model_family} must have artifact role {expected_role}"
            )
        save_final_bundle(bundle, paths[model_family])
    return paths


def fit_and_evaluate_final_model(
    prepared: PreparedFinalData,
    configuration: FrozenFinalConfiguration,
) -> FinalTestEvaluation:
    """Fit and evaluate exactly one frozen model at threshold 0.5."""

    if configuration.threshold != DEFAULT_THRESHOLD:
        raise ValueError("T12 requires the unchanged default threshold of 0.5")
    estimator = build_final_estimator(configuration)
    estimator.fit(prepared.X_development, prepared.y_development)
    probabilities_array = positive_class_probability(estimator, prepared.X_test)
    predictions_array = np.where(
        probabilities_array >= configuration.threshold,
        configuration.positive_class,
        configuration.negative_class,
    )
    probabilities = pd.Series(
        probabilities_array,
        index=prepared.y_test.index,
        name=f"{configuration.model_family} positive probability",
    )
    predictions = pd.Series(
        predictions_array,
        index=prepared.y_test.index,
        name=f"{configuration.model_family} prediction",
    )
    metrics = calculate_binary_metrics(prepared.y_test, predictions, probabilities)
    row: dict[str, object] = {
        "Model": configuration.model_family,
        "Selected feature variant": configuration.feature_variant,
        "Processed feature count": prepared.X_development.shape[1],
        "Development rows": len(prepared.X_development),
        "Test rows": len(prepared.X_test),
        "Threshold": configuration.threshold,
    }
    row.update(metrics)
    metadata = {
        "project": "IT3051 FDM Mini Project",
        "model_version": "T12-final-v1",
        "model_family": configuration.model_family,
        "artifact_role": "final",
        "hyperparameters": deepcopy(configuration.hyperparameters),
        "execution_settings": final_execution_settings(configuration.model_family),
        "feature_variant": configuration.feature_variant,
        "scale_numeric": configuration.scale_numeric,
        "positive_class": configuration.positive_class,
        "negative_class": configuration.negative_class,
        "threshold": configuration.threshold,
        "selection_rule": configuration.selection_rule,
        "test_consulted_during_selection": configuration.test_consulted,
        "development_first_date": pd.to_datetime(prepared.dates_development)
        .min()
        .date()
        .isoformat(),
        "development_last_date": pd.to_datetime(prepared.dates_development)
        .max()
        .date()
        .isoformat(),
        "development_rows": len(prepared.X_development),
        "test_first_date": pd.to_datetime(prepared.dates_test).min().date().isoformat(),
        "test_last_date": pd.to_datetime(prepared.dates_test).max().date().isoformat(),
        "test_rows_evaluated": len(prepared.X_test),
        "processed_feature_count": prepared.X_development.shape[1],
        "expected_raw_columns": [DATE_COLUMN, *predictor_columns()],
        "contains_test_labels": False,
        "post_test_model_changes": False,
    }
    bundle = FinalRainfallModelBundle(
        estimator=estimator,
        preprocessor=prepared.preprocessor,
        configuration=configuration,
        processed_feature_names=tuple(prepared.X_development.columns),
        expected_raw_columns=(DATE_COLUMN, *predictor_columns()),
        metadata=metadata,
    )
    return FinalTestEvaluation(
        bundle=bundle,
        comparison=pd.DataFrame([row]),
        predictions=predictions,
        positive_probabilities=probabilities,
    )


def compare_validation_and_test(
    configuration: FrozenFinalConfiguration,
    test_metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Compare frozen selection evidence with final holdout metrics."""

    if len(test_metrics) != 1:
        raise ValueError("Exactly one final Test result is required")
    rows = []
    for metric in COMPARISON_METRICS:
        validation_value = float(configuration.validation_metrics[metric])
        test_value = float(test_metrics.iloc[0][metric])
        delta = test_value - validation_value
        direction = "Improved" if delta > 0 else "Declined" if delta < 0 else "Unchanged"
        rows.append(
            {
                "Metric": metric,
                "T11 Validation": validation_value,
                "Final Test": test_value,
                "Test minus Validation": delta,
                "Direction": direction,
            }
        )
    return pd.DataFrame(rows)


def save_final_bundle(bundle: FinalRainfallModelBundle, path: str | Path) -> Path:
    """Persist the frozen estimator and preprocessing state."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination, compress=3)
    return destination


def load_final_bundle(path: str | Path) -> FinalRainfallModelBundle:
    """Load and validate the serialized final bundle type."""

    loaded = joblib.load(Path(path))
    if not isinstance(loaded, FinalRainfallModelBundle):
        raise TypeError("Serialized artifact is not a FinalRainfallModelBundle")
    return loaded


def artifact_metadata_table(
    bundle: FinalRainfallModelBundle,
    artifact_path: str | Path,
    labels_match: bool,
    probabilities_match: bool,
) -> pd.DataFrame:
    """Create a compact machine-readable artifact and round-trip record."""

    path = Path(artifact_path)
    return pd.DataFrame(
        [
            {
                "Artifact path": path.as_posix(),
                "Artifact bytes": path.stat().st_size,
                "Bundle type": type(bundle).__name__,
                "Model version": bundle.metadata["model_version"],
                "Model family": bundle.configuration.model_family,
                "Exact hyperparameters": json.dumps(
                    bundle.configuration.hyperparameters,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "Execution-only settings": json.dumps(
                    bundle.metadata["execution_settings"],
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "Feature variant": bundle.configuration.feature_variant,
                "Processed feature count": len(bundle.processed_feature_names),
                "Development rows": bundle.metadata["development_rows"],
                "Development date range": (
                    f"{bundle.metadata['development_first_date']} to "
                    f"{bundle.metadata['development_last_date']}"
                ),
                "Test evaluation date range": (
                    f"{bundle.metadata['test_first_date']} to "
                    f"{bundle.metadata['test_last_date']}"
                ),
                "Positive class": bundle.configuration.positive_class,
                "Threshold": bundle.configuration.threshold,
                "Contains Test labels": "No",
                "Round-trip labels match": "Yes" if labels_match else "No",
                "Round-trip probabilities match": (
                    "Yes" if probabilities_match else "No"
                ),
            }
        ]
    )


def save_final_figures(
    evaluation: FinalTestEvaluation,
    y_test: pd.Series,
    validation_test_comparison: pd.DataFrame,
    output_directory: str | Path,
) -> list[Path]:
    """Save four Test figures for only the frozen selected final model."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    model_name = evaluation.bundle.configuration.model_family

    counts = confusion_matrix(
        y_test, evaluation.predictions, labels=[NEGATIVE_LABEL, POSITIVE_LABEL]
    )
    fig, axis = plt.subplots(figsize=(6.5, 5.5), constrained_layout=True)
    image = axis.imshow(counts, cmap="Blues")
    threshold = counts.max() / 2
    for row in range(2):
        for column in range(2):
            axis.text(
                column,
                row,
                f"{counts[row, column]:,}",
                ha="center",
                va="center",
                color="white" if counts[row, column] > threshold else "black",
                fontsize=13,
            )
    axis.set_xticks([0, 1], labels=[NEGATIVE_LABEL, POSITIVE_LABEL])
    axis.set_yticks([0, 1], labels=[NEGATIVE_LABEL, POSITIVE_LABEL])
    axis.set_xlabel("Predicted RainTomorrow")
    axis.set_ylabel("Actual RainTomorrow")
    axis.set_title(f"Final Test Confusion Matrix — {model_name}")
    fig.colorbar(image, ax=axis, label="Test rows")
    path = output / "12_final_test_confusion_matrix.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    saved.append(path)

    binary_test = (np.asarray(y_test) == POSITIVE_LABEL).astype(int)
    false_positive_rate, true_positive_rate, _ = roc_curve(
        binary_test, evaluation.positive_probabilities
    )
    roc_auc = float(evaluation.comparison.iloc[0]["ROC-AUC"])
    fig, axis = plt.subplots(figsize=(7, 5.5), constrained_layout=True)
    axis.plot(false_positive_rate, true_positive_rate, label=f"{model_name} ({roc_auc:.3f})")
    axis.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Chance")
    axis.set(xlabel="False-positive rate", ylabel="True-positive rate", title="Final Test ROC Curve")
    axis.legend(loc="lower right")
    axis.grid(alpha=0.25)
    path = output / "12_final_test_roc_curve.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    saved.append(path)

    precision, recall, _ = precision_recall_curve(
        binary_test, evaluation.positive_probabilities
    )
    pr_auc = float(evaluation.comparison.iloc[0]["PR-AUC"])
    prevalence = float(binary_test.mean())
    fig, axis = plt.subplots(figsize=(7, 5.5), constrained_layout=True)
    axis.plot(recall, precision, label=f"{model_name} ({pr_auc:.3f})")
    axis.axhline(prevalence, linestyle="--", color="grey", label=f"Prevalence ({prevalence:.3f})")
    axis.set(
        xlabel="Recall for RainTomorrow=Yes",
        ylabel="Precision for RainTomorrow=Yes",
        title="Final Test Precision–Recall Curve",
    )
    axis.legend(loc="lower left")
    axis.grid(alpha=0.25)
    path = output / "12_final_test_precision_recall_curve.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    saved.append(path)

    plot = validation_test_comparison.set_index("Metric")
    x = np.arange(len(plot))
    width = 0.38
    fig, axis = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    axis.bar(x - width / 2, plot["T11 Validation"], width, label="T11 Validation")
    axis.bar(x + width / 2, plot["Final Test"], width, label="Final Test")
    axis.set_xticks(x, labels=plot.index, rotation=20, ha="right")
    axis.set_ylim(0, 1)
    axis.set_ylabel("Metric value")
    axis.set_title(f"Validation vs Final Test — {model_name}")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    path = output / "12_validation_vs_test_metrics.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    saved.append(path)
    return saved
