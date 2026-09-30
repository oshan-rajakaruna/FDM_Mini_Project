"""Leakage-safe, date-aware hyperparameter tuning utilities for T10.

Hyperparameters are selected only with expanding-window folds inside Train.
Every fold fits feature preprocessing on its own fold-training rows. The final
selected configurations are refitted on complete Train and evaluated once on
Validation. No function in this module accepts the held-out Test subset.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve
from sklearn.model_selection import ParameterGrid, ParameterSampler, TimeSeriesSplit
from sklearn.tree import DecisionTreeClassifier

from fdm_rainfall.features import WeatherFeatureEngineer
from fdm_rainfall.modeling import (
    METRIC_COLUMNS,
    MODEL_NAMES,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    RANDOM_STATE,
    calculate_binary_metrics,
    positive_class_probability,
)
from fdm_rainfall.preprocessing import (
    DATE_COLUMN,
    RainfallPreprocessor,
    separate_supervised_components,
)


PRIMARY_METRIC = "PR-AUC"
CV_REPORT_METRICS = (
    "PR-AUC",
    "ROC-AUC",
    "F1 (Yes)",
    "Recall (Yes)",
    "Balanced Accuracy",
)
COMPARISON_METRICS = (
    "Accuracy",
    "Balanced Accuracy",
    "Precision (Yes)",
    "Recall (Yes)",
    "F1 (Yes)",
    "ROC-AUC",
    "PR-AUC",
)


@dataclass(frozen=True)
class DateAwareFold:
    """Row positions for one whole-date expanding-window fold."""

    fold: int
    train_positions: np.ndarray
    validation_positions: np.ndarray


@dataclass(frozen=True)
class PreparedFold:
    """One fold after fold-training-only T08 preprocessing."""

    fold: int
    scale_numeric: bool
    feature_engineer: WeatherFeatureEngineer
    preprocessor: RainfallPreprocessor
    X_train: pd.DataFrame
    X_validation: pd.DataFrame
    y_train: pd.Series
    y_validation: pd.Series
    dates_train: pd.Series
    dates_validation: pd.Series


@dataclass(frozen=True)
class TuningConfiguration:
    """Bounded search definition for one existing model family."""

    model_name: str
    scale_numeric: bool
    search_method: str
    parameter_space: dict[str, list[Any]]
    n_iter: int | None = None


@dataclass(frozen=True)
class SearchResult:
    """Fold-level and aggregate results for one model-family search."""

    configuration: TuningConfiguration
    candidates: list[dict[str, Any]]
    fold_results: pd.DataFrame
    summary: pd.DataFrame
    best_parameters: dict[str, Any]
    best_cv_pr_auc: float
    best_cv_pr_auc_std: float
    runtime_seconds: float


@dataclass(frozen=True)
class TunedEvaluation:
    """Validation-only results from four Train-CV-selected configurations."""

    fitted_models: dict[str, ClassifierMixin]
    comparison: pd.DataFrame
    predictions: dict[str, pd.Series]
    positive_probabilities: dict[str, pd.Series]
    execution_times: pd.DataFrame


def date_aware_expanding_window_splits(
    dates: pd.Series,
    n_splits: int = 3,
) -> list[DateAwareFold]:
    """Split rows by unique dates into non-shuffled expanding windows."""

    parsed = pd.to_datetime(dates, errors="coerce")
    if parsed.isna().any():
        raise ValueError("Dates must be complete and parseable for chronological CV")
    unique_dates = pd.Index(parsed.unique()).sort_values()
    if len(unique_dates) < n_splits + 1:
        raise ValueError("Insufficient unique dates for the requested number of folds")

    splitter = TimeSeriesSplit(n_splits=n_splits)
    folds: list[DateAwareFold] = []
    for fold_number, (train_date_positions, validation_date_positions) in enumerate(
        splitter.split(unique_dates),
        start=1,
    ):
        train_dates = unique_dates[train_date_positions]
        validation_dates = unique_dates[validation_date_positions]
        train_positions = np.flatnonzero(parsed.isin(train_dates).to_numpy())
        validation_positions = np.flatnonzero(parsed.isin(validation_dates).to_numpy())
        if len(np.intersect1d(train_positions, validation_positions)):
            raise RuntimeError("CV fold row overlap detected")
        if set(train_dates).intersection(validation_dates):
            raise RuntimeError("CV fold date overlap detected")
        if train_dates.max() >= validation_dates.min():
            raise RuntimeError("CV fold chronology is not strictly ordered")
        folds.append(
            DateAwareFold(
                fold=fold_number,
                train_positions=train_positions,
                validation_positions=validation_positions,
            )
        )
    return folds


def cv_fold_boundary_table(
    dates: pd.Series,
    folds: list[DateAwareFold],
) -> pd.DataFrame:
    """Summarize exact date and row boundaries for each expanding fold."""

    parsed = pd.to_datetime(dates, errors="raise")
    rows: list[dict[str, object]] = []
    for fold in folds:
        train_dates = parsed.iloc[fold.train_positions]
        validation_dates = parsed.iloc[fold.validation_positions]
        rows.append(
            {
                "Fold": fold.fold,
                "Train first date": train_dates.min().date().isoformat(),
                "Train last date": train_dates.max().date().isoformat(),
                "Validation first date": validation_dates.min().date().isoformat(),
                "Validation last date": validation_dates.max().date().isoformat(),
                "Train rows": len(fold.train_positions),
                "Validation rows": len(fold.validation_positions),
                "Train unique dates": train_dates.nunique(),
                "Validation unique dates": validation_dates.nunique(),
                "Row overlap": len(
                    np.intersect1d(fold.train_positions, fold.validation_positions)
                ),
                "Date overlap": len(set(train_dates).intersection(validation_dates)),
                "Strict chronology": bool(train_dates.max() < validation_dates.min()),
            }
        )
    return pd.DataFrame(rows)


def prepare_engineered_train_validation(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    scale_numeric: bool,
    fold: int = 0,
) -> PreparedFold:
    """Fit T08 preprocessing on supplied Train rows and transform Validation."""

    train = separate_supervised_components(train_frame)
    validation = separate_supervised_components(validation_frame)
    raw_train = pd.concat([train.dates.rename(DATE_COLUMN), train.X], axis=1)
    raw_validation = pd.concat(
        [validation.dates.rename(DATE_COLUMN), validation.X],
        axis=1,
    )

    engineer = WeatherFeatureEngineer(output="default").fit(raw_train)
    engineered_train = engineer.transform(raw_train)
    engineered_validation = engineer.transform(raw_validation)
    preprocessor = RainfallPreprocessor(
        scale_numeric=scale_numeric,
        configuration="engineered",
    )
    X_train = preprocessor.fit_transform(engineered_train)
    X_validation = preprocessor.transform(engineered_validation)
    if list(X_train.columns) != list(X_validation.columns):
        raise RuntimeError("Fold Train and Validation processed schemas differ")
    return PreparedFold(
        fold=fold,
        scale_numeric=scale_numeric,
        feature_engineer=engineer,
        preprocessor=preprocessor,
        X_train=X_train,
        X_validation=X_validation,
        y_train=train.y,
        y_validation=validation.y,
        dates_train=train.dates,
        dates_validation=validation.dates,
    )


def prepare_cv_folds(
    train_frame: pd.DataFrame,
    folds: list[DateAwareFold],
    scale_numeric: bool,
) -> list[PreparedFold]:
    """Prepare all CV folds without fitting on later Train-period rows."""

    return [
        prepare_engineered_train_validation(
            train_frame.iloc[fold.train_positions].copy(),
            train_frame.iloc[fold.validation_positions].copy(),
            scale_numeric=scale_numeric,
            fold=fold.fold,
        )
        for fold in folds
    ]


def build_tuning_configurations() -> dict[str, TuningConfiguration]:
    """Return bounded, reproducible searches for exactly four model families."""

    return {
        "Logistic Regression": TuningConfiguration(
            model_name="Logistic Regression",
            scale_numeric=True,
            search_method="Exhaustive grid",
            parameter_space={
                "C": [0.01, 0.1, 1.0, 10.0],
                "class_weight": [None, "balanced"],
            },
        ),
        "Decision Tree": TuningConfiguration(
            model_name="Decision Tree",
            scale_numeric=False,
            search_method="Deterministic randomized",
            parameter_space={
                "criterion": ["gini", "entropy"],
                "max_depth": [None, 5, 10, 20],
                "min_samples_split": [2, 20, 50],
                "min_samples_leaf": [1, 5, 20],
                "class_weight": [None, "balanced"],
            },
            n_iter=12,
        ),
        "Random Forest": TuningConfiguration(
            model_name="Random Forest",
            scale_numeric=False,
            search_method="Deterministic randomized",
            parameter_space={
                "n_estimators": [100, 150],
                "max_depth": [None, 10, 20],
                "min_samples_split": [2, 20],
                "min_samples_leaf": [1, 5],
                "max_features": ["sqrt", 0.5],
                "class_weight": [None, "balanced"],
            },
            n_iter=8,
        ),
        "Gradient Boosting": TuningConfiguration(
            model_name="Gradient Boosting",
            scale_numeric=False,
            search_method="Deterministic randomized",
            parameter_space={
                "n_estimators": [50, 100],
                "learning_rate": [0.03, 0.05, 0.1],
                "max_depth": [2, 3],
                "min_samples_split": [2, 20],
                "min_samples_leaf": [1, 5],
                "subsample": [0.8, 1.0],
            },
            n_iter=6,
        ),
    }


def candidate_parameters(configuration: TuningConfiguration) -> list[dict[str, Any]]:
    """Materialize the deterministic candidate list for a configuration."""

    if configuration.search_method == "Exhaustive grid":
        return [dict(params) for params in ParameterGrid(configuration.parameter_space)]
    if configuration.search_method == "Deterministic randomized":
        if configuration.n_iter is None:
            raise ValueError("Randomized configuration requires n_iter")
        return [
            dict(params)
            for params in ParameterSampler(
                configuration.parameter_space,
                n_iter=configuration.n_iter,
                random_state=RANDOM_STATE,
            )
        ]
    raise ValueError(f"Unknown search method: {configuration.search_method}")


def build_tuned_model(model_name: str, parameters: dict[str, Any]) -> ClassifierMixin:
    """Construct one configured estimator from an existing T09 model family."""

    if model_name == "Logistic Regression":
        model: ClassifierMixin = LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    elif model_name == "Decision Tree":
        model = DecisionTreeClassifier(random_state=RANDOM_STATE)
    elif model_name == "Random Forest":
        model = RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1)
    elif model_name == "Gradient Boosting":
        model = GradientBoostingClassifier(random_state=RANDOM_STATE)
    else:
        raise ValueError(f"Unsupported model family: {model_name}")
    model.set_params(**parameters)
    return model


def _parameter_json(parameters: dict[str, Any]) -> str:
    return json.dumps(parameters, sort_keys=True, separators=(",", ":"))


def summarize_cv_results(fold_results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate folds and rank only by mean PR-AUC.

    Candidate number is a neutral deterministic tie-break for an exact mean
    PR-AUC tie; no other performance metric influences candidate selection.
    """

    rows: list[dict[str, object]] = []
    for (candidate_id, parameters), group in fold_results.groupby(
        ["Candidate", "Parameters"],
        sort=True,
    ):
        row: dict[str, object] = {
            "Candidate": int(candidate_id),
            "Parameters": parameters,
            "Folds": int(len(group)),
            "Total fit seconds": float(group["Fit seconds"].sum()),
        }
        for metric in CV_REPORT_METRICS:
            row[f"CV {metric} mean"] = float(group[metric].mean())
            row[f"CV {metric} std"] = float(group[metric].std(ddof=0))
        rows.append(row)
    summary = pd.DataFrame(rows)
    return summary.sort_values(
        ["CV PR-AUC mean", "Candidate"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def run_tuning_search(
    configuration: TuningConfiguration,
    prepared_folds: list[PreparedFold],
) -> SearchResult:
    """Evaluate bounded candidates on fold-specific preprocessed Train folds."""

    if not prepared_folds:
        raise ValueError("At least one prepared CV fold is required")
    if any(fold.scale_numeric != configuration.scale_numeric for fold in prepared_folds):
        raise ValueError("Prepared-fold scaling does not match model configuration")

    candidates = candidate_parameters(configuration)
    rows: list[dict[str, object]] = []
    search_start = perf_counter()
    for candidate_id, parameters in enumerate(candidates, start=1):
        for fold in prepared_folds:
            model = build_tuned_model(configuration.model_name, parameters)
            fit_start = perf_counter()
            model.fit(fold.X_train, fold.y_train)
            fit_seconds = perf_counter() - fit_start
            prediction = model.predict(fold.X_validation)
            probability = positive_class_probability(model, fold.X_validation)
            metrics = calculate_binary_metrics(
                fold.y_validation,
                prediction,
                probability,
            )
            row: dict[str, object] = {
                "Model": configuration.model_name,
                "Candidate": candidate_id,
                "Parameters": _parameter_json(parameters),
                "Fold": fold.fold,
                "Fit seconds": fit_seconds,
            }
            row.update({metric: metrics[metric] for metric in CV_REPORT_METRICS})
            rows.append(row)

    runtime = perf_counter() - search_start
    fold_results = pd.DataFrame(rows)
    summary = summarize_cv_results(fold_results)
    best_row = summary.iloc[0]
    best_parameters = json.loads(str(best_row["Parameters"]))
    return SearchResult(
        configuration=configuration,
        candidates=candidates,
        fold_results=fold_results,
        summary=summary,
        best_parameters=best_parameters,
        best_cv_pr_auc=float(best_row["CV PR-AUC mean"]),
        best_cv_pr_auc_std=float(best_row["CV PR-AUC std"]),
        runtime_seconds=runtime,
    )


def tuning_configuration_table(n_splits: int = 3) -> pd.DataFrame:
    """Summarize search method, space, candidate count, and fit count."""

    rows = []
    for configuration in build_tuning_configurations().values():
        candidates = candidate_parameters(configuration)
        rows.append(
            {
                "Model": configuration.model_name,
                "Representation": (
                    "T08 engineered, scaled"
                    if configuration.scale_numeric
                    else "T08 engineered, unscaled"
                ),
                "Search method": configuration.search_method,
                "Primary metric": "Average Precision (PR-AUC)",
                "Candidates": len(candidates),
                "CV folds": n_splits,
                "Model fits": len(candidates) * n_splits,
                "Parameter space": _parameter_json(configuration.parameter_space),
            }
        )
    return pd.DataFrame(rows)


def best_parameter_table(results: dict[str, SearchResult]) -> pd.DataFrame:
    """Build one compact best-search-result row per model family."""

    rows = []
    for model_name in MODEL_NAMES:
        result = results[model_name]
        rows.append(
            {
                "Model": model_name,
                "Best parameters": _parameter_json(result.best_parameters),
                "Best CV PR-AUC mean": result.best_cv_pr_auc,
                "Best CV PR-AUC std": result.best_cv_pr_auc_std,
                "Candidates": len(result.candidates),
                "CV folds": int(result.fold_results["Fold"].nunique()),
                "Model fits": len(result.fold_results),
                "Search method": result.configuration.search_method,
                "Search runtime seconds": result.runtime_seconds,
            }
        )
    return pd.DataFrame(rows)


def fit_and_evaluate_tuned_models(
    best_parameters: dict[str, dict[str, Any]],
    scaled_data: PreparedFold,
    unscaled_data: PreparedFold,
) -> TunedEvaluation:
    """Refit selected configurations on Train and evaluate Validation once."""

    if not scaled_data.scale_numeric or unscaled_data.scale_numeric:
        raise ValueError("Expected scaled then unscaled prepared data")
    fitted_models: dict[str, ClassifierMixin] = {}
    predictions: dict[str, pd.Series] = {}
    probabilities: dict[str, pd.Series] = {}
    rows: list[dict[str, object]] = []
    timing_rows: list[dict[str, object]] = []

    for model_name in MODEL_NAMES:
        data = scaled_data if model_name == "Logistic Regression" else unscaled_data
        model = build_tuned_model(model_name, best_parameters[model_name])
        fit_start = perf_counter()
        model.fit(data.X_train, data.y_train)
        fit_seconds = perf_counter() - fit_start
        prediction_start = perf_counter()
        prediction = pd.Series(
            model.predict(data.X_validation),
            index=data.y_validation.index,
            name=model_name,
        )
        probability = pd.Series(
            positive_class_probability(model, data.X_validation),
            index=data.y_validation.index,
            name=model_name,
        )
        prediction_seconds = perf_counter() - prediction_start
        row: dict[str, object] = {"Model": model_name}
        row.update(calculate_binary_metrics(data.y_validation, prediction, probability))
        rows.append(row)
        fitted_models[model_name] = model
        predictions[model_name] = prediction
        probabilities[model_name] = probability
        timing_rows.append(
            {
                "Model": model_name,
                "Final Train fit seconds": fit_seconds,
                "Validation prediction and probability seconds": prediction_seconds,
            }
        )

    return TunedEvaluation(
        fitted_models=fitted_models,
        comparison=pd.DataFrame(rows).loc[:, ["Model", *METRIC_COLUMNS]],
        predictions=predictions,
        positive_probabilities=probabilities,
        execution_times=pd.DataFrame(timing_rows),
    )


def compare_baseline_and_tuned(
    baseline: pd.DataFrame,
    tuned: pd.DataFrame,
) -> pd.DataFrame:
    """Return baseline, tuned, and absolute change for required metrics."""

    baseline_indexed = baseline.set_index("Model")
    tuned_indexed = tuned.set_index("Model")
    if set(baseline_indexed.index) != set(MODEL_NAMES):
        raise ValueError("Baseline comparison must contain exactly four model families")
    if set(tuned_indexed.index) != set(MODEL_NAMES):
        raise ValueError("Tuned comparison must contain exactly four model families")

    rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        row: dict[str, object] = {"Model": model_name}
        for metric in COMPARISON_METRICS:
            baseline_value = float(baseline_indexed.loc[model_name, metric])
            tuned_value = float(tuned_indexed.loc[model_name, metric])
            row[f"Baseline {metric}"] = baseline_value
            row[f"Tuned {metric}"] = tuned_value
            row[f"Change {metric}"] = tuned_value - baseline_value
        rows.append(row)
    return pd.DataFrame(rows)


def save_tuned_figures(
    evaluation: TunedEvaluation,
    y_validation: pd.Series,
    baseline_comparison: pd.DataFrame,
    output_directory: str | Path,
) -> list[Path]:
    """Save four Validation-only tuned-model figure groups."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    for axis, model_name in zip(axes.flat, MODEL_NAMES, strict=True):
        counts = confusion_matrix(
            y_validation,
            evaluation.predictions[model_name],
            labels=[NEGATIVE_LABEL, POSITIVE_LABEL],
        )
        image = axis.imshow(counts, cmap="Purples")
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
                )
        axis.set_title(model_name)
        axis.set_xlabel("Predicted label")
        axis.set_ylabel("Actual label")
        axis.set_xticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
        axis.set_yticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
    fig.colorbar(image, ax=axes, shrink=0.8, label="Validation rows")
    fig.suptitle("T10 Tuned Validation Confusion Matrices")
    path = output / "10_tuned_validation_confusion_matrices.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    binary_validation = (np.asarray(y_validation) == POSITIVE_LABEL).astype(int)
    fig, axis = plt.subplots(figsize=(8, 6))
    for model_name in MODEL_NAMES:
        false_positive_rate, true_positive_rate, _ = roc_curve(
            binary_validation,
            evaluation.positive_probabilities[model_name],
        )
        value = float(
            evaluation.comparison.loc[
                evaluation.comparison["Model"] == model_name, "ROC-AUC"
            ].iloc[0]
        )
        axis.plot(false_positive_rate, true_positive_rate, label=f"{model_name} ({value:.3f})")
    axis.plot([0, 1], [0, 1], linestyle="--", color="grey", label="No-skill")
    axis.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="Tuned Validation ROC Curves")
    axis.legend(loc="lower right")
    axis.grid(alpha=0.25)
    path = output / "10_tuned_validation_roc_curves.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    fig, axis = plt.subplots(figsize=(8, 6))
    prevalence = float(binary_validation.mean())
    for model_name in MODEL_NAMES:
        precision, recall, _ = precision_recall_curve(
            binary_validation,
            evaluation.positive_probabilities[model_name],
        )
        value = float(
            evaluation.comparison.loc[
                evaluation.comparison["Model"] == model_name, "PR-AUC"
            ].iloc[0]
        )
        axis.plot(recall, precision, label=f"{model_name} ({value:.3f})")
    axis.axhline(prevalence, linestyle="--", color="grey", label=f"Prevalence ({prevalence:.3f})")
    axis.set(
        xlabel="Recall for RainTomorrow=Yes",
        ylabel="Precision for RainTomorrow=Yes",
        title="Tuned Validation Precision-Recall Curves",
    )
    axis.legend(loc="lower left")
    axis.grid(alpha=0.25)
    path = output / "10_tuned_validation_precision_recall_curves.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    metrics = list(COMPARISON_METRICS)
    baseline_values = baseline_comparison.set_index("Model")
    tuned_values = evaluation.comparison.set_index("Model")
    positions = np.arange(len(MODEL_NAMES))
    width = 0.055
    fig, axis = plt.subplots(figsize=(14, 7))
    for metric_index, metric in enumerate(metrics):
        offset = (metric_index - (len(metrics) - 1) / 2) * width * 2.1
        axis.bar(
            positions + offset - width / 2,
            baseline_values.loc[list(MODEL_NAMES), metric],
            width,
            alpha=0.45,
            label=f"Baseline {metric}",
        )
        axis.bar(
            positions + offset + width / 2,
            tuned_values.loc[list(MODEL_NAMES), metric],
            width,
            label=f"Tuned {metric}",
        )
    axis.set(
        xticks=positions,
        xticklabels=MODEL_NAMES,
        ylabel="Validation metric value",
        title="T09 Baseline vs T10 Tuned Validation Metrics",
        ylim=(0, 1),
    )
    axis.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=8)
    axis.grid(axis="y", alpha=0.25)
    path = output / "10_baseline_vs_tuned_validation_metrics.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)
    return saved
