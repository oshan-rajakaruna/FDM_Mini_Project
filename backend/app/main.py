"""FastAPI application entry point for the RainWise backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import ApiInfoResponse, HealthResponse


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
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
