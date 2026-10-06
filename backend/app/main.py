"""FastAPI application entry point for the RainWise backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .model_service import ModelLoadError, get_model_service
from .schemas import ApiInfoResponse, HealthResponse


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
