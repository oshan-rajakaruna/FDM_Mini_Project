"""Runtime configuration for the RainWise API."""

from dataclasses import dataclass, field
import os
from pathlib import Path


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_cors_origins() -> tuple[str, ...]:
    configured_origins = os.getenv("RAINWISE_CORS_ORIGINS", "")
    if not configured_origins.strip():
        return DEFAULT_CORS_ORIGINS

    return tuple(
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    )


def _read_project_path(environment_variable: str, default: Path) -> Path:
    """Resolve a configurable project path without depending on the launch directory."""

    configured_path = os.getenv(environment_variable, "").strip()
    path = Path(configured_path).expanduser() if configured_path else default
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for the API and its frozen model artifact."""

    app_name: str = "RainWise API"
    app_version: str = "0.1.0"
    app_description: str = "Backend foundation for RainWise weather-risk decision support."
    cors_origins: tuple[str, ...] = field(default_factory=_read_cors_origins)
    model_artifact_path: Path = field(
        default_factory=lambda: _read_project_path(
            "RAINWISE_MODEL_PATH",
            PROJECT_ROOT / "models" / "final_rainfall_model.joblib",
        )
    )
    model_source_path: Path = field(
        default_factory=lambda: _read_project_path(
            "RAINWISE_MODEL_SOURCE_PATH",
            PROJECT_ROOT / "src",
        )
    )


settings = Settings()
