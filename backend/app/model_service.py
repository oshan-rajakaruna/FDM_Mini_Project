"""Load and validate the frozen RainWise model bundle once per API process."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

from .config import Settings, settings


EXPECTED_MODEL_FAMILY = "Random Forest"
EXPECTED_ESTIMATOR_CLASS = "RandomForestClassifier"
EXPECTED_FEATURE_VARIANT = "V0_DEFAULT"
EXPECTED_SCALING_MODE = "unscaled"
EXPECTED_THRESHOLD = 0.5
EXPECTED_POSITIVE_CLASS = "Yes"
EXPECTED_FEATURE_COUNT = 89
EXPECTED_ARTIFACT_ROLE = "final"
EXPECTED_RANDOM_STATE = 42


class ModelLoadError(RuntimeError):
    """Raised when the configured model artifact cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Safe deployment metadata retained for internal backend use."""

    model_type: str
    representation: str
    scaling: str
    threshold: float
    positive_class: str
    feature_count: int
    training_role: str


class ModelService:
    """Own the validated model bundle and its safe metadata."""

    __slots__ = ("_bundle", "metadata")

    def __init__(self, bundle: Any, metadata: ModelMetadata) -> None:
        self._bundle = bundle
        self.metadata = metadata

    @property
    def bundle(self) -> Any:
        """Return the frozen bundle for a future prediction service."""

        return self._bundle


def _make_project_package_importable(source_path: Path) -> None:
    if not source_path.is_dir():
        raise ModelLoadError(
            f"Configured model source directory does not exist: {source_path}"
        )

    source = str(source_path)
    if source not in sys.path:
        sys.path.insert(0, source)


def _validate_bundle(bundle: Any) -> ModelMetadata:
    configuration = bundle.configuration
    artifact_metadata = bundle.metadata
    feature_count = len(bundle.processed_feature_names)
    estimator_class = type(bundle.estimator).__name__

    checks = {
        "model family": (configuration.model_family, EXPECTED_MODEL_FAMILY),
        "estimator class": (estimator_class, EXPECTED_ESTIMATOR_CLASS),
        "artifact role": (
            artifact_metadata.get("artifact_role"),
            EXPECTED_ARTIFACT_ROLE,
        ),
        "feature representation": (
            configuration.feature_variant,
            EXPECTED_FEATURE_VARIANT,
        ),
        "scaling mode": (
            artifact_metadata.get("scaling_mode"),
            EXPECTED_SCALING_MODE,
        ),
        "classification threshold": (
            configuration.threshold,
            EXPECTED_THRESHOLD,
        ),
        "positive class": (
            configuration.positive_class,
            EXPECTED_POSITIVE_CLASS,
        ),
        "processed feature count": (feature_count, EXPECTED_FEATURE_COUNT),
        "metadata feature count": (
            artifact_metadata.get("processed_feature_count"),
            EXPECTED_FEATURE_COUNT,
        ),
        "random state": (
            configuration.hyperparameters.get("random_state"),
            EXPECTED_RANDOM_STATE,
        ),
        "metadata random state": (
            artifact_metadata.get("hyperparameters", {}).get("random_state"),
            EXPECTED_RANDOM_STATE,
        ),
    }
    mismatches = [
        f"{name}={actual!r} (expected {expected!r})"
        for name, (actual, expected) in checks.items()
        if actual != expected
    ]

    if configuration.scale_numeric is not False:
        mismatches.append(
            f"scale_numeric={configuration.scale_numeric!r} (expected False)"
        )
    if configuration.test_consulted is not False:
        mismatches.append(
            f"test_consulted={configuration.test_consulted!r} (expected False)"
        )
    if artifact_metadata.get("test_used_for_artifact_fitting") is not False:
        mismatches.append(
            "test_used_for_artifact_fitting must be False"
        )

    if mismatches:
        raise ModelLoadError(
            "Configured artifact is not the expected final RainWise bundle: "
            + "; ".join(mismatches)
        )

    return ModelMetadata(
        model_type=configuration.model_family,
        representation=configuration.feature_variant,
        scaling=artifact_metadata["scaling_mode"],
        threshold=float(configuration.threshold),
        positive_class=configuration.positive_class,
        feature_count=feature_count,
        training_role=artifact_metadata["artifact_role"],
    )


def _load_model_service(runtime_settings: Settings) -> ModelService:
    artifact_path = runtime_settings.model_artifact_path
    if not artifact_path.is_file():
        raise ModelLoadError(f"Model artifact does not exist: {artifact_path}")

    _make_project_package_importable(runtime_settings.model_source_path)
    try:
        from fdm_rainfall.final_model import load_final_bundle
    except Exception as exc:
        raise ModelLoadError(
            "Unable to import the RainWise model bundle definitions. "
            "Install backend/requirements.txt and verify "
            f"RAINWISE_MODEL_SOURCE_PATH. Original error: {exc}"
        ) from exc

    try:
        bundle = load_final_bundle(artifact_path)
    except Exception as exc:
        raise ModelLoadError(
            f"Unable to load model artifact at {artifact_path}: {exc}"
        ) from exc

    try:
        metadata = _validate_bundle(bundle)
    except ModelLoadError:
        raise
    except Exception as exc:
        raise ModelLoadError(
            f"Model artifact metadata could not be validated: {exc}"
        ) from exc

    return ModelService(bundle=bundle, metadata=metadata)


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Return the process-wide model service, loading the artifact only once."""

    return _load_model_service(settings)
