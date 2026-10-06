"""FastAPI application entry point for the RainWise backend."""

from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import (
    MongoService,
    MongoServiceError,
    get_mongo_service,
)
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
    ReadinessChecks,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize process-level model and database services."""

    mongo_service: MongoService | None = None
    try:
        application.state.model_service = get_model_service()
    except ModelLoadError as exc:
        raise RuntimeError(f"RainWise model startup failed: {exc}") from exc

    try:
        mongo_service = get_mongo_service()
        mongo_service.connect()
        application.state.mongo_service = mongo_service
    except MongoServiceError as exc:
        if mongo_service is not None:
            mongo_service.close()
        raise RuntimeError(f"RainWise database startup failed: {exc}") from None

    try:
        yield
    finally:
        mongo_service.close()


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
def health_check(request: Request, response: Response) -> HealthResponse:
    """Report secret-free readiness for the API, model, and database."""

    model_ready = getattr(request.app.state, "model_service", None) is not None
    mongo_service = getattr(request.app.state, "mongo_service", None)
    database_ready = mongo_service is not None and mongo_service.ping()
    ready = model_ready and database_ready

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if ready else "degraded",
        service="rainwise-backend",
        version=settings.app_version,
        checks=ReadinessChecks(
            backend="ready",
            model="ready" if model_ready else "not_ready",
            database="ready" if database_ready else "not_ready",
        ),
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
