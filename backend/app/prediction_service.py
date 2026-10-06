"""Prediction orchestration through the persisted RainWise model bundle."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .model_service import ModelService
from .schemas import PredictionRequest


class PredictionInputError(ValueError):
    """Raised when input is structurally valid but unsupported by the bundle."""


class PredictionServiceError(RuntimeError):
    """Raised when the saved model cannot produce a valid prediction."""


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Validated result returned by the saved model."""

    prediction: str
    rain_probability: float
    threshold: float
    positive_class: str


def _known_locations(bundle: object) -> set[str]:
    """Read the fitted Location vocabulary from the persisted preprocessor."""

    try:
        preprocessor = bundle.preprocessor.base_preprocessor_
        location_index = tuple(preprocessor.categorical_predictors_).index("Location")
        categories = preprocessor.categorical_categories_[location_index]
    except (AttributeError, ValueError, IndexError) as exc:
        raise PredictionServiceError(
            "Saved RainWise model does not expose its fitted Location vocabulary."
        ) from exc
    return {str(value) for value in categories if str(value) != "Missing"}


def _to_model_frame(
    request: PredictionRequest,
    model_service: ModelService,
) -> pd.DataFrame:
    """Represent one request as raw columns expected by the persisted bundle."""

    bundle = model_service.bundle
    request_values = request.model_dump(mode="python")
    expected_columns = tuple(bundle.expected_raw_columns)
    if set(request_values) != set(expected_columns):
        missing = sorted(set(expected_columns).difference(request_values))
        extra = sorted(set(request_values).difference(expected_columns))
        raise PredictionServiceError(
            f"Backend/model raw schema mismatch; missing={missing}, extra={extra}"
        )

    if request.Location not in _known_locations(bundle):
        raise PredictionInputError(
            f"Location {request.Location!r} is not supported by the saved model."
        )

    request_values["Date"] = request.Date.isoformat()
    raw_row = {
        field: np.nan if request_values[field] is None else request_values[field]
        for field in expected_columns
    }
    return pd.DataFrame([raw_row], columns=expected_columns)


def predict_rainfall(
    request: PredictionRequest,
    model_service: ModelService,
) -> PredictionResult:
    """Run one raw observation through the bundle's own inference methods."""

    try:
        raw_input = _to_model_frame(request, model_service)
        bundle = model_service.bundle
        probabilities = bundle.predict_positive_probability(raw_input)
        predictions = bundle.predict(raw_input)
    except PredictionInputError:
        raise
    except PredictionServiceError:
        raise
    except Exception as exc:
        raise PredictionServiceError(
            "Saved RainWise model could not produce a prediction."
        ) from exc

    if len(probabilities) != 1 or len(predictions) != 1:
        raise PredictionServiceError(
            "Saved RainWise model returned an unexpected result shape."
        )

    probability = float(probabilities[0])
    prediction = str(predictions[0])
    if not np.isfinite(probability) or not 0 <= probability <= 1:
        raise PredictionServiceError(
            "Saved RainWise model returned an invalid rain probability."
        )
    if prediction not in {"Yes", "No"}:
        raise PredictionServiceError(
            "Saved RainWise model returned an unsupported class label."
        )

    return PredictionResult(
        prediction=prediction,
        rain_probability=probability,
        threshold=model_service.metadata.threshold,
        positive_class=model_service.metadata.positive_class,
    )
