"""Runtime configuration for the RainWise API."""

from dataclasses import dataclass, field
import os


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


def _read_cors_origins() -> tuple[str, ...]:
    configured_origins = os.getenv("RAINWISE_CORS_ORIGINS", "")
    if not configured_origins.strip():
        return DEFAULT_CORS_ORIGINS

    return tuple(
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """API settings kept separate from future model configuration."""

    app_name: str = "RainWise API"
    app_version: str = "0.1.0"
    app_description: str = "Backend foundation for RainWise weather-risk decision support."
    cors_origins: tuple[str, ...] = field(default_factory=_read_cors_origins)


settings = Settings()
