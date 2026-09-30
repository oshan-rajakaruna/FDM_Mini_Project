"""Controlled, leakage-safe feature-representation optimization for T11."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.metrics import confusion_matrix, precision_recall_curve
from sklearn.preprocessing import StandardScaler

from fdm_rainfall.features import DEFAULT_ENGINEERED_PREDICTORS, WeatherFeatureEngineer
from fdm_rainfall.modeling import (
    MODEL_NAMES,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    calculate_binary_metrics,
    positive_class_probability,
)
from fdm_rainfall.preprocessing import (
    DATE_COLUMN,
    RainfallPreprocessor,
    separate_supervised_components,
)
from fdm_rainfall.tuning import DateAwareFold, build_tuned_model


VARIANT_ORDER = (
    "V0_DEFAULT",
    "V1_ADD_YEAR",
    "V2_LOG_RAINFALL_REPLACE",
    "V3_YEAR_AND_LOG_RAINFALL",
)

T10_TUNED_PARAMETERS: dict[str, dict[str, Any]] = {
    "Logistic Regression": {"C": 0.1, "class_weight": None},
    "Decision Tree": {
        "criterion": "gini",
        "max_depth": 10,
        "min_samples_split": 20,
        "min_samples_leaf": 20,
        "class_weight": "balanced",
    },
    "Random Forest": {
        "n_estimators": 150,
        "max_depth": 20,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": None,
    },
    "Gradient Boosting": {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 3,
        "min_samples_split": 20,
        "min_samples_leaf": 5,
        "subsample": 0.8,
    },
}

CV_METRICS = (
    "PR-AUC",
    "ROC-AUC",
    "Balanced Accuracy",
    "Precision (Yes)",
    "Recall (Yes)",
    "F1 (Yes)",
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
class VariantDefinition:
    name: str
    add_year: bool
    log_rainfall_replace: bool


@dataclass(frozen=True)
class PreparedVariantFold:
    fold: int
    variant: str
    scale_numeric: bool
    preprocessor: "FeatureVariantPreprocessor"
    X_train: pd.DataFrame
    X_validation: pd.DataFrame
    y_train: pd.Series
    y_validation: pd.Series
    dates_train: pd.Series
    dates_validation: pd.Series


@dataclass(frozen=True)
class FeatureExperimentResult:
    fold_results: pd.DataFrame
    runtime_summary: pd.DataFrame


@dataclass(frozen=True)
class FinalFeatureEvaluation:
    fitted_models: dict[str, ClassifierMixin]
    comparison: pd.DataFrame
    predictions: dict[str, pd.Series]
    positive_probabilities: dict[str, pd.Series]
    execution_times: pd.DataFrame


def feature_variant_definitions() -> dict[str, VariantDefinition]:
    """Return exactly the four controlled T11 representations."""

    return {
        "V0_DEFAULT": VariantDefinition("V0_DEFAULT", False, False),
        "V1_ADD_YEAR": VariantDefinition("V1_ADD_YEAR", True, False),
        "V2_LOG_RAINFALL_REPLACE": VariantDefinition(
            "V2_LOG_RAINFALL_REPLACE", False, True
        ),
        "V3_YEAR_AND_LOG_RAINFALL": VariantDefinition(
            "V3_YEAR_AND_LOG_RAINFALL", True, True
        ),
    }


def variant_feature_names(variant: str) -> tuple[str, ...]:
    """Return the deterministic preprocessed-input schema for a variant."""

    definition = feature_variant_definitions()[variant]
    names = list(DEFAULT_ENGINEERED_PREDICTORS)
    if definition.log_rainfall_replace:
        names[names.index("Rainfall")] = "Rainfall_log1p"
    if definition.add_year:
        names.append("Year")
    return tuple(names)


def apply_feature_variant(raw_predictors: pd.DataFrame, variant: str) -> pd.DataFrame:
    """Create one target-independent T11 representation without mutation."""

    definition = feature_variant_definitions()[variant]
    if "RainTomorrow" in raw_predictors.columns:
        raise ValueError("RainTomorrow must be separated before feature optimization")
    source = raw_predictors.copy(deep=True)
    default = WeatherFeatureEngineer(output="default").fit_transform(source)
    result = default.copy(deep=True)
    dates = pd.to_datetime(source[DATE_COLUMN], format="%Y-%m-%d", errors="coerce")
    if dates.isna().any():
        raise ValueError("Date contains invalid or missing YYYY-MM-DD values")
    if definition.log_rainfall_replace:
        observed = result["Rainfall"].dropna()
        if (observed < 0).any():
            raise ValueError("Rainfall_log1p requires non-negative observed Rainfall")
        result["Rainfall_log1p"] = np.log1p(result.pop("Rainfall"))
    if definition.add_year:
        result["Year"] = dates.dt.year.astype(float)
    return result.loc[:, variant_feature_names(variant)].copy(deep=True)


class FeatureVariantPreprocessor:
    """Reuse T08 preprocessing and add fold-local support for Year/log Rainfall."""

    def __init__(self, variant: str, scale_numeric: bool) -> None:
        self.variant = variant
        self.scale_numeric = bool(scale_numeric)
        self.definition = feature_variant_definitions()[variant]
        self.is_fitted_ = False

    def _validate(self, frame: pd.DataFrame) -> None:
        expected = set(variant_feature_names(self.variant))
        if set(frame.columns) != expected:
            missing = sorted(expected.difference(frame.columns))
            extra = sorted(set(frame.columns).difference(expected))
            raise ValueError(f"Variant schema mismatch; missing={missing}, extra={extra}")

    def _base_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        base = frame.drop(columns=["Year"], errors="ignore").copy(deep=True)
        if self.definition.log_rainfall_replace:
            base = base.rename(columns={"Rainfall_log1p": "Rainfall"})
        return base.loc[:, DEFAULT_ENGINEERED_PREDICTORS]

    def fit(self, X_train: pd.DataFrame) -> "FeatureVariantPreprocessor":
        self._validate(X_train)
        train = X_train.loc[:, variant_feature_names(self.variant)].copy(deep=True)
        self.fit_row_count_ = int(len(train))
        self.fit_index_ = train.index.copy()
        self.base_preprocessor_ = RainfallPreprocessor(
            scale_numeric=self.scale_numeric,
            configuration="engineered",
        ).fit(self._base_frame(train))
        self.year_median_: float | None = None
        self.year_scaler_: StandardScaler | None = None
        if self.definition.add_year:
            self.year_median_ = float(train["Year"].median())
            if not np.isfinite(self.year_median_):
                raise ValueError("Fold Train has no valid Year values")
            year = train[["Year"]].fillna(self.year_median_)
            if self.scale_numeric:
                self.year_scaler_ = StandardScaler().fit(year)
        names = list(self.base_preprocessor_.get_feature_names_out())
        if self.definition.log_rainfall_replace:
            names[names.index("Rainfall")] = "Rainfall_log1p"
        if self.definition.add_year:
            names.append("Year")
        self.feature_names_out_ = names
        self.is_fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted_:
            raise RuntimeError("FeatureVariantPreprocessor must be fitted first")
        self._validate(X)
        source = X.loc[:, variant_feature_names(self.variant)].copy(deep=True)
        transformed = self.base_preprocessor_.transform(self._base_frame(source))
        if self.definition.log_rainfall_replace:
            transformed = transformed.rename(columns={"Rainfall": "Rainfall_log1p"})
        if self.definition.add_year:
            year = source[["Year"]].fillna(self.year_median_)
            values = (
                self.year_scaler_.transform(year)
                if self.year_scaler_ is not None
                else year.to_numpy(dtype=float)
            )
            transformed["Year"] = values[:, 0]
        transformed = transformed.loc[:, self.feature_names_out_]
        if transformed.isna().any().any() or not np.isfinite(
            transformed.to_numpy(dtype=float)
        ).all():
            raise ValueError("Variant preprocessing produced non-finite values")
        return transformed

    def fit_transform(self, X_train: pd.DataFrame) -> pd.DataFrame:
        return self.fit(X_train).transform(X_train)


def prepare_variant_train_validation(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    variant: str,
    scale_numeric: bool,
    fold: int = 0,
) -> PreparedVariantFold:
    """Fit a variant preprocessor on supplied Train rows only."""

    train = separate_supervised_components(train_frame)
    validation = separate_supervised_components(validation_frame)
    raw_train = pd.concat([train.dates.rename(DATE_COLUMN), train.X], axis=1)
    raw_validation = pd.concat(
        [validation.dates.rename(DATE_COLUMN), validation.X], axis=1
    )
    engineered_train = apply_feature_variant(raw_train, variant)
    engineered_validation = apply_feature_variant(raw_validation, variant)
    preprocessor = FeatureVariantPreprocessor(variant, scale_numeric)
    X_train = preprocessor.fit_transform(engineered_train)
    X_validation = preprocessor.transform(engineered_validation)
    if list(X_train.columns) != list(X_validation.columns):
        raise RuntimeError("Variant Train and Validation schemas differ")
    return PreparedVariantFold(
        fold=fold,
        variant=variant,
        scale_numeric=scale_numeric,
        preprocessor=preprocessor,
        X_train=X_train,
        X_validation=X_validation,
        y_train=train.y,
        y_validation=validation.y,
        dates_train=train.dates,
        dates_validation=validation.dates,
    )


def prepare_all_variant_folds(
    train_frame: pd.DataFrame,
    folds: list[DateAwareFold],
) -> dict[str, dict[str, list[PreparedVariantFold]]]:
    """Prepare scaled/unscaled fold-local matrices for every T11 variant."""

    prepared: dict[str, dict[str, list[PreparedVariantFold]]] = {}
    for variant in VARIANT_ORDER:
        prepared[variant] = {}
        for label, scaled in (("scaled", True), ("unscaled", False)):
            prepared[variant][label] = [
                prepare_variant_train_validation(
                    train_frame.iloc[fold.train_positions].copy(),
                    train_frame.iloc[fold.validation_positions].copy(),
                    variant,
                    scaled,
                    fold.fold,
                )
                for fold in folds
            ]
    return prepared


def run_feature_experiment(
    prepared: dict[str, dict[str, list[PreparedVariantFold]]],
) -> FeatureExperimentResult:
    """Run the fixed 4-model x 4-variant x 3-fold experiment."""

    rows: list[dict[str, object]] = []
    runtime_rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        route = "scaled" if model_name == "Logistic Regression" else "unscaled"
        for variant in VARIANT_ORDER:
            combination_start = perf_counter()
            folds = prepared[variant][route]
            for fold in folds:
                model = build_tuned_model(model_name, T10_TUNED_PARAMETERS[model_name])
                fit_start = perf_counter()
                model.fit(fold.X_train, fold.y_train)
                prediction = model.predict(fold.X_validation)
                probability = positive_class_probability(model, fold.X_validation)
                fit_predict_seconds = perf_counter() - fit_start
                metrics = calculate_binary_metrics(
                    fold.y_validation, prediction, probability
                )
                row: dict[str, object] = {
                    "Model": model_name,
                    "Variant": variant,
                    "Fold": fold.fold,
                    "Train first date": pd.to_datetime(fold.dates_train).min().date().isoformat(),
                    "Train last date": pd.to_datetime(fold.dates_train).max().date().isoformat(),
                    "Validation first date": pd.to_datetime(
                        fold.dates_validation
                    ).min().date().isoformat(),
                    "Validation last date": pd.to_datetime(
                        fold.dates_validation
                    ).max().date().isoformat(),
                    "Train rows": len(fold.X_train),
                    "Validation rows": len(fold.X_validation),
                    "Processed feature count": fold.X_train.shape[1],
                    "Runtime seconds": fit_predict_seconds,
                }
                row.update({metric: metrics[metric] for metric in CV_METRICS})
                rows.append(row)
            runtime_rows.append(
                {
                    "Model": model_name,
                    "Variant": variant,
                    "CV folds": len(folds),
                    "Runtime seconds": perf_counter() - combination_start,
                }
            )
    return FeatureExperimentResult(
        fold_results=pd.DataFrame(rows),
        runtime_summary=pd.DataFrame(runtime_rows),
    )


def summarize_feature_experiment(fold_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize every model/variant combination without selecting on Validation."""

    rows: list[dict[str, object]] = []
    for (model, variant), group in fold_results.groupby(["Model", "Variant"]):
        row: dict[str, object] = {
            "Model": model,
            "Variant": variant,
            "CV folds": int(len(group)),
            "Processed features min": int(group["Processed feature count"].min()),
            "Processed features max": int(group["Processed feature count"].max()),
            "Runtime seconds": float(group["Runtime seconds"].sum()),
        }
        for metric in CV_METRICS:
            row[f"CV {metric} mean"] = float(group[metric].mean())
            row[f"CV {metric} std"] = float(group[metric].std(ddof=0))
        rows.append(row)
    result = pd.DataFrame(rows)
    model_order = {name: position for position, name in enumerate(MODEL_NAMES)}
    variant_order = {name: position for position, name in enumerate(VARIANT_ORDER)}
    return result.sort_values(
        ["Model", "Variant"],
        key=lambda column: column.map(
            model_order if column.name == "Model" else variant_order
        ),
        kind="mergesort",
    ).reset_index(drop=True)


def select_feature_variants(summary: pd.DataFrame) -> pd.DataFrame:
    """Select by mean CV PR-AUC only; variant order breaks exact ties."""

    order = {name: position for position, name in enumerate(VARIANT_ORDER)}
    rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        candidates = summary.loc[summary["Model"] == model_name].copy()
        if set(candidates["Variant"]) != set(VARIANT_ORDER):
            raise ValueError("Each model must contain exactly four feature variants")
        candidates["_variant_order"] = candidates["Variant"].map(order)
        candidates = candidates.sort_values(
            ["CV PR-AUC mean", "_variant_order"],
            ascending=[False, True],
            kind="mergesort",
        )
        winner = candidates.iloc[0]
        default = candidates.loc[candidates["Variant"] == "V0_DEFAULT"].iloc[0]
        exact_ties = int(
            (candidates["CV PR-AUC mean"] == winner["CV PR-AUC mean"]).sum()
        )
        rows.append(
            {
                "Model": model_name,
                "Selected feature variant": winner["Variant"],
                "Mean CV PR-AUC": float(winner["CV PR-AUC mean"]),
                "CV PR-AUC std": float(winner["CV PR-AUC std"]),
                "Difference versus V0 default": float(
                    winner["CV PR-AUC mean"] - default["CV PR-AUC mean"]
                ),
                "Tie-break required": "Yes" if exact_ties > 1 else "No",
            }
        )
    return pd.DataFrame(rows)


def fit_selected_variants_on_validation(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    winners: pd.DataFrame,
) -> FinalFeatureEvaluation:
    """Refit fixed T10 models on complete Train and evaluate Validation once."""

    selected = winners.set_index("Model")["Selected feature variant"].to_dict()
    fitted: dict[str, ClassifierMixin] = {}
    predictions: dict[str, pd.Series] = {}
    probabilities: dict[str, pd.Series] = {}
    metric_rows: list[dict[str, object]] = []
    timing_rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        variant = str(selected[model_name])
        prepared = prepare_variant_train_validation(
            train_frame,
            validation_frame,
            variant,
            scale_numeric=model_name == "Logistic Regression",
        )
        model = build_tuned_model(model_name, T10_TUNED_PARAMETERS[model_name])
        start = perf_counter()
        model.fit(prepared.X_train, prepared.y_train)
        prediction = pd.Series(
            model.predict(prepared.X_validation),
            index=prepared.y_validation.index,
            name=model_name,
        )
        probability = pd.Series(
            positive_class_probability(model, prepared.X_validation),
            index=prepared.y_validation.index,
            name=model_name,
        )
        seconds = perf_counter() - start
        row: dict[str, object] = {
            "Model": model_name,
            "Selected feature variant": variant,
            "Processed feature count": prepared.X_train.shape[1],
        }
        row.update(
            calculate_binary_metrics(prepared.y_validation, prediction, probability)
        )
        metric_rows.append(row)
        timing_rows.append(
            {
                "Model": model_name,
                "Selected feature variant": variant,
                "Final fit and Validation prediction seconds": seconds,
            }
        )
        fitted[model_name] = model
        predictions[model_name] = prediction
        probabilities[model_name] = probability
    return FinalFeatureEvaluation(
        fitted_models=fitted,
        comparison=pd.DataFrame(metric_rows),
        predictions=predictions,
        positive_probabilities=probabilities,
        execution_times=pd.DataFrame(timing_rows),
    )


def compare_t09_t10_t11(
    baseline: pd.DataFrame,
    tuned_default: pd.DataFrame,
    feature_optimized: pd.DataFrame,
) -> pd.DataFrame:
    """Create a descriptive T09/T10/T11 Validation comparison."""

    indexed = {
        "T09 Baseline": baseline.set_index("Model"),
        "T10 Tuned default": tuned_default.set_index("Model"),
        "T11 Selected representation": feature_optimized.set_index("Model"),
    }
    rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        row: dict[str, object] = {"Model": model_name}
        for metric in COMPARISON_METRICS:
            t09 = float(indexed["T09 Baseline"].loc[model_name, metric])
            t10 = float(indexed["T10 Tuned default"].loc[model_name, metric])
            t11 = float(indexed["T11 Selected representation"].loc[model_name, metric])
            row[f"T09 {metric}"] = t09
            row[f"T10 {metric}"] = t10
            row[f"T11 {metric}"] = t11
            row[f"T10 minus T09 {metric}"] = t10 - t09
            row[f"T11 minus T10 {metric}"] = t11 - t10
            row[f"T11 minus T09 {metric}"] = t11 - t09
        rows.append(row)
    return pd.DataFrame(rows)


def save_feature_optimization_figures(
    summary: pd.DataFrame,
    final: FinalFeatureEvaluation,
    y_validation: pd.Series,
    tuned_default: pd.DataFrame,
    output_directory: str | Path,
) -> list[Path]:
    """Save four Train-CV/Validation-only T11 figure groups."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    fig, axis = plt.subplots(figsize=(12, 6))
    positions = np.arange(len(MODEL_NAMES))
    width = 0.19
    for index, variant in enumerate(VARIANT_ORDER):
        values = summary.loc[summary["Variant"] == variant].set_index("Model")
        axis.bar(
            positions + (index - 1.5) * width,
            values.loc[list(MODEL_NAMES), "CV PR-AUC mean"],
            width,
            yerr=values.loc[list(MODEL_NAMES), "CV PR-AUC std"],
            capsize=3,
            label=variant,
        )
    axis.set(
        xticks=positions,
        xticklabels=MODEL_NAMES,
        ylabel="Mean Train-CV PR-AUC",
        title="T11 Train-CV PR-AUC by Feature Variant",
    )
    axis.legend(fontsize=8)
    axis.grid(axis="y", alpha=0.25)
    path = output / "11_train_cv_pr_auc_by_variant.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    metrics = ["Balanced Accuracy", "Precision (Yes)", "Recall (Yes)", "F1 (Yes)", "ROC-AUC", "PR-AUC"]
    t10 = tuned_default.set_index("Model")
    t11 = final.comparison.set_index("Model")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for axis, metric in zip(axes.flat, metrics, strict=True):
        x = np.arange(len(MODEL_NAMES))
        axis.bar(x - 0.18, t10.loc[list(MODEL_NAMES), metric], 0.36, label="T10 default")
        axis.bar(x + 0.18, t11.loc[list(MODEL_NAMES), metric], 0.36, label="T11 selected")
        axis.set_title(metric)
        axis.set_xticks(x, ["LR", "DT", "RF", "GB"])
        axis.set_ylim(0, 1)
        axis.grid(axis="y", alpha=0.25)
    axes.flat[0].legend()
    path = output / "11_t10_vs_t11_validation_metrics.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    for axis, model_name in zip(axes.flat, MODEL_NAMES, strict=True):
        counts = confusion_matrix(
            y_validation,
            final.predictions[model_name],
            labels=[NEGATIVE_LABEL, POSITIVE_LABEL],
        )
        image = axis.imshow(counts, cmap="Blues")
        for row in range(2):
            for column in range(2):
                axis.text(column, row, f"{counts[row, column]:,}", ha="center", va="center")
        axis.set_title(model_name)
        axis.set_xlabel("Predicted label")
        axis.set_ylabel("Actual label")
        axis.set_xticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
        axis.set_yticks([0, 1], [NEGATIVE_LABEL, POSITIVE_LABEL])
    fig.colorbar(image, ax=axes, shrink=0.8, label="Validation rows")
    fig.suptitle("T11 Selected-Representation Validation Confusion Matrices")
    path = output / "11_validation_confusion_matrices.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    binary_validation = (np.asarray(y_validation) == POSITIVE_LABEL).astype(int)
    fig, axis = plt.subplots(figsize=(8, 6))
    for model_name in MODEL_NAMES:
        precision, recall, _ = precision_recall_curve(
            binary_validation, final.positive_probabilities[model_name]
        )
        value = float(
            final.comparison.loc[final.comparison["Model"] == model_name, "PR-AUC"].iloc[0]
        )
        axis.plot(recall, precision, label=f"{model_name} ({value:.3f})")
    prevalence = float(binary_validation.mean())
    axis.axhline(prevalence, linestyle="--", color="grey", label=f"Prevalence ({prevalence:.3f})")
    axis.set(
        xlabel="Recall for RainTomorrow=Yes",
        ylabel="Precision for RainTomorrow=Yes",
        title="T11 Selected-Representation Validation PR Curves",
    )
    axis.legend(loc="lower left")
    axis.grid(alpha=0.25)
    path = output / "11_validation_precision_recall_curves.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)
    return saved
