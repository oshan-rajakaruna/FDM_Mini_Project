"""Response schemas for RainWise system endpoints."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: Literal["ok"]
    service: str
    version: str


class ApiInfoResponse(BaseModel):
    """Basic API information returned at the service root."""

    name: str
    version: str
    status: Literal["available"]
    documentation: str
