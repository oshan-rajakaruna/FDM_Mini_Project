"""Leakage-safe baseline classification utilities for T09.

This module deliberately exposes a Train/Validation-only workflow. The held-out
Test subset is not accepted by any baseline evaluation function.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.tree import DecisionTreeClassifier


NEGATIVE_LABEL = "No"
POSITIVE_LABEL = "Yes"
RANDOM_STATE = 42

MODEL_NAMES = (
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
    "Gradient Boosting",
)

METRIC_COLUMNS = (
    "Accuracy",
    "Balanced Accuracy",
    "Precision (Yes)",
    "Recall (Yes)",
    "F1 (Yes)",
    "ROC-AUC",
    "PR-AUC",
    "TN",
    "FP",
    "FN",
    "TP",
)


@dataclass(frozen=True)
class BaselineEvaluation:
    """Validation-only outputs from the four fitted baseline classifiers."""

    fitted_models: dict[str, ClassifierMixin]
    comparison: pd.DataFrame
    predictions: dict[str, pd.Series]
    positive_probabilities: dict[str, pd.Series]
    execution_times: pd.DataFrame


def build_baseline_models() -> dict[str, ClassifierMixin]:
    """Construct exactly the four required essentially-default baselines.

    ``max_iter=1000`` is a convergence safeguard for Logistic Regression.
    Random states make stochastic fitting reproducible, and ``n_jobs=-1`` on
    Random Forest is an execution-only parallelism setting.
    """

    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
        ),
        "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
    }


def positive_class_probability(
    model: ClassifierMixin,
    X: pd.DataFrame,
    positive_label: str = POSITIVE_LABEL,
) -> np.ndarray:
    """Return the probability column matched to ``positive_label`` safely."""

    if not hasattr(model, "classes_"):
        raise ValueError("Model must be fitted before positive probabilities are extracted")
    classes = np.asarray(model.classes_)
    matches = np.flatnonzero(classes == positive_label)
    if len(matches) != 1:
        raise ValueError(f"Positive class {positive_label!r} is absent or ambiguous in model.classes_")
    probabilities = np.asarray(model.predict_proba(X))
    if probabilities.ndim != 2 or probabilities.shape[1] != len(classes):
        raise ValueError("predict_proba output does not match model.classes_")
    return probabilities[:, int(matches[0])]


def confusion_counts(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, int]:
    """Return binary confusion counts in the explicit TN, FP, FN, TP order."""

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[NEGATIVE_LABEL, POSITIVE_LABEL],
    ).ravel()
    return {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}


def calculate_binary_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    positive_probabilities: pd.Series | np.ndarray,
) -> dict[str, float | int]:
    """Calculate required validation metrics with Yes as the positive class."""

    y_true_array = np.asarray(y_true)
    y_pred_array = np.asarray(y_pred)
    probabilities = np.asarray(positive_probabilities, dtype=float)
    if not (len(y_true_array) == len(y_pred_array) == len(probabilities)):
        raise ValueError("Targets, predictions, and probabilities must have equal lengths")
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Positive-class probabilities must be finite and within [0, 1]")
    observed_labels = set(pd.unique(y_true_array))
    if observed_labels != {NEGATIVE_LABEL, POSITIVE_LABEL}:
        raise ValueError("y_true must contain both 'No' and 'Yes' labels")

    binary_true = (y_true_array == POSITIVE_LABEL).astype(int)
    metrics: dict[str, float | int] = {
        "Accuracy": float(accuracy_score(y_true_array, y_pred_array)),
        "Balanced Accuracy": float(balanced_accuracy_score(y_true_array, y_pred_array)),
        "Precision (Yes)": float(
            precision_score(
                y_true_array,
                y_pred_array,
                pos_label=POSITIVE_LABEL,
                zero_division=0,
            )
        ),
        "Recall (Yes)": float(
            recall_score(
                y_true_array,
                y_pred_array,
                pos_label=POSITIVE_LABEL,
                zero_division=0,
            )
        ),
        "F1 (Yes)": float(
            f1_score(
                y_true_array,
                y_pred_array,
                pos_label=POSITIVE_LABEL,
                zero_division=0,
            )
        ),
        "ROC-AUC": float(roc_auc_score(binary_true, probabilities)),
        "PR-AUC": float(average_precision_score(binary_true, probabilities)),
    }
    metrics.update(confusion_counts(y_true_array, y_pred_array))
    return metrics


def _validate_aligned_inputs(X: pd.DataFrame, y: pd.Series, name: str) -> None:
    if len(X) != len(y):
        raise ValueError(f"{name} predictors and target have different row counts")
    if not X.index.equals(y.index):
        raise ValueError(f"{name} predictors and target indexes are not aligned")
    if X.isna().any().any() or not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError(f"{name} predictors must be finite and fully preprocessed")


def fit_and_evaluate_baselines(
    X_train_scaled: pd.DataFrame,
    X_validation_scaled: pd.DataFrame,
    X_train_unscaled: pd.DataFrame,
    X_validation_unscaled: pd.DataFrame,
    y_train: pd.Series,
    y_validation: pd.Series,
) -> BaselineEvaluation:
    """Fit on Train and evaluate only on Validation.

    Logistic Regression uses the scaled engineered representation. The three
    tree-based algorithms use the unscaled engineered representation. This
    signature intentionally has no Test-set arguments.
    """

    for X, y, name in (
        (X_train_scaled, y_train, "scaled Train"),
        (X_validation_scaled, y_validation, "scaled Validation"),
        (X_train_unscaled, y_train, "unscaled Train"),
        (X_validation_unscaled, y_validation, "unscaled Validation"),
    ):
        _validate_aligned_inputs(X, y, name)
    if list(X_train_scaled.columns) != list(X_validation_scaled.columns):
        raise ValueError("Scaled Train and Validation schemas differ")
    if list(X_train_unscaled.columns) != list(X_validation_unscaled.columns):
        raise ValueError("Unscaled Train and Validation schemas differ")
    if list(X_train_scaled.columns) != list(X_train_unscaled.columns):
        raise ValueError("Scaled and unscaled engineered schemas differ")

    fitted_models = build_baseline_models()
    rows: list[dict[str, object]] = []
    predictions: dict[str, pd.Series] = {}
    positive_probabilities: dict[str, pd.Series] = {}
    timing_rows: list[dict[str, object]] = []

    for model_name, model in fitted_models.items():
        uses_scaled = model_name == "Logistic Regression"
        X_train = X_train_scaled if uses_scaled else X_train_unscaled
        X_validation = X_validation_scaled if uses_scaled else X_validation_unscaled
        fit_start = perf_counter()
        model.fit(X_train, y_train)
        fit_seconds = perf_counter() - fit_start
        prediction_start = perf_counter()
        prediction = pd.Series(
            model.predict(X_validation),
            index=y_validation.index,
            name=model_name,
        )
        probability = pd.Series(
            positive_class_probability(model, X_validation),
            index=y_validation.index,
            name=model_name,
        )
        prediction_seconds = perf_counter() - prediction_start
        row: dict[str, object] = {"Model": model_name}
        row.update(calculate_binary_metrics(y_validation, prediction, probability))
        rows.append(row)
        predictions[model_name] = prediction
        positive_probabilities[model_name] = probability
        timing_rows.append(
            {
                "Model": model_name,
                "Fit seconds": fit_seconds,
                "Validation prediction and probability seconds": prediction_seconds,
            }
        )

    comparison = pd.DataFrame(rows).loc[:, ["Model", *METRIC_COLUMNS]]
    return BaselineEvaluation(
        fitted_models=fitted_models,
        comparison=comparison,
        predictions=predictions,
        positive_probabilities=positive_probabilities,
        execution_times=pd.DataFrame(timing_rows),
    )


def baseline_configuration_table() -> pd.DataFrame:
    """Return the documented representation and execution settings."""

    return pd.DataFrame(
        [
            {
                "Model": "Logistic Regression",
                "Representation": "T08 engineered, scaled",
                "Non-default execution settings": "max_iter=1000; random_state=42",
                "Purpose": "Interpretable linear reference baseline",
            },
            {
                "Model": "Decision Tree",
                "Representation": "T08 engineered, unscaled",
                "Non-default execution settings": "random_state=42",
                "Purpose": "Single nonlinear tree baseline",
            },
            {
                "Model": "Random Forest",
                "Representation": "T08 engineered, unscaled",
                "Non-default execution settings": "random_state=42; n_jobs=-1",
                "Purpose": "Bagging ensemble baseline",
            },
            {
                "Model": "Gradient Boosting",
                "Representation": "T08 engineered, unscaled",
                "Non-default execution settings": "random_state=42",
                "Purpose": "Boosting ensemble baseline",
            },
        ]
    )


def save_baseline_figures(
    evaluation: BaselineEvaluation,
    y_validation: pd.Series,
    output_directory: str | Path,
) -> list[Path]:
    """Save the four required validation-only baseline figure groups."""

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
        image = axis.imshow(counts, cmap="Blues")
        contrast_threshold = counts.max() / 2
        for row in range(2):
            for column in range(2):
                axis.text(
                    column,
                    row,
                    f"{counts[row, column]:,}",
                    ha="center",
                    va="center",
                    color="white" if counts[row, column] > contrast_threshold else "black",
                )
        axis.set_title(model_name)
        axis.set_xlabel("Predicted label")
        axis.set_ylabel("Actual label")
        axis.set_xticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
        axis.set_yticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
    fig.colorbar(image, ax=axes, shrink=0.8, label="Validation rows")
    fig.suptitle("T09 Validation Confusion Matrices")
    path = output / "09_validation_confusion_matrices.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    binary_validation = (np.asarray(y_validation) == POSITIVE_LABEL).astype(int)
    fig, axis = plt.subplots(figsize=(8, 6))
    for model_name in MODEL_NAMES:
        probability = evaluation.positive_probabilities[model_name]
        false_positive_rate, true_positive_rate, _ = roc_curve(binary_validation, probability)
        auc = float(
            evaluation.comparison.loc[
                evaluation.comparison["Model"] == model_name, "ROC-AUC"
            ].iloc[0]
        )
        axis.plot(false_positive_rate, true_positive_rate, label=f"{model_name} ({auc:.3f})")
    axis.plot([0, 1], [0, 1], linestyle="--", color="grey", label="No-skill")
    axis.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="Validation ROC Curves")
    axis.legend(loc="lower right")
    axis.grid(alpha=0.25)
    path = output / "09_validation_roc_curves.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    fig, axis = plt.subplots(figsize=(8, 6))
    prevalence = float(binary_validation.mean())
    for model_name in MODEL_NAMES:
        probability = evaluation.positive_probabilities[model_name]
        precision, recall, _ = precision_recall_curve(binary_validation, probability)
        auc = float(
            evaluation.comparison.loc[
                evaluation.comparison["Model"] == model_name, "PR-AUC"
            ].iloc[0]
        )
        axis.plot(recall, precision, label=f"{model_name} ({auc:.3f})")
    axis.axhline(prevalence, linestyle="--", color="grey", label=f"Prevalence ({prevalence:.3f})")
    axis.set(
        xlabel="Recall for RainTomorrow=Yes",
        ylabel="Precision for RainTomorrow=Yes",
        title="Validation Precision-Recall Curves",
    )
    axis.legend(loc="lower left")
    axis.grid(alpha=0.25)
    path = output / "09_validation_precision_recall_curves.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    display_metrics = [
        "Accuracy",
        "Balanced Accuracy",
        "Precision (Yes)",
        "Recall (Yes)",
        "F1 (Yes)",
        "ROC-AUC",
        "PR-AUC",
    ]
    plot_data = evaluation.comparison.set_index("Model").loc[:, display_metrics]
    fig, axis = plt.subplots(figsize=(12, 7))
    plot_data.plot(kind="bar", ax=axis, width=0.8)
    axis.set(
        xlabel="Baseline model",
        ylabel="Validation metric value",
        title="T09 Validation Metric Comparison",
        ylim=(0, 1),
    )
    axis.tick_params(axis="x", rotation=0)
    axis.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    axis.grid(axis="y", alpha=0.25)
    path = output / "09_validation_metric_comparison.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)
    return saved
