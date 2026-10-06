"""FastAPI application entry point for the RainWise backend."""

from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .model_service import ModelLoadError, ModelService, get_model_service
from .prediction_service import (
    PredictionInputError,
    PredictionServiceError,
    predict_rainfall,
)
from .schemas import (
    ApiInfoResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Validate and retain the frozen model once when the API starts."""

    try:
        application.state.model_service = get_model_service()
    except ModelLoadError as exc:
        raise RuntimeError(f"RainWise model startup failed: {exc}") from exc
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiInfoResponse, tags=["System"])
def api_info() -> ApiInfoResponse:
    """Return API metadata without initializing prediction services."""

    return ApiInfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        status="available",
        documentation="/docs",
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Confirm that the API process is available."""

    return HealthResponse(
        status="ok",
        service="rainwise-backend",
        version=settings.app_version,
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(
    request: PredictionRequest,
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> PredictionResponse:
    """Predict next-day rain using the persisted model's inference pipeline."""

    try:
        result = predict_rainfall(request, model_service)
    except PredictionInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except PredictionServiceError as exc:
        logger.exception("RainWise prediction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return PredictionResponse(
        prediction=result.prediction,
        rain_probability=result.rain_probability,
        threshold=result.threshold,
        positive_class=result.positive_class,
    )
