"""Response schemas for RainWise system endpoints."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


WindDirection = Literal[
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]
Temperature = Annotated[float, Field(ge=-100, le=70, allow_inf_nan=False)]
NonNegativeMeasurement = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Humidity = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Pressure = Annotated[float, Field(gt=0, allow_inf_nan=False)]
CloudCover = Annotated[float, Field(ge=0, le=8, allow_inf_nan=False)]


class PredictionRequest(BaseModel):
    """The 22 raw weather inputs accepted by the frozen model bundle."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    Date: date
    Location: Annotated[str, Field(min_length=1, max_length=64)]
    RainToday: Literal["Yes", "No"] | None = None
    MinTemp: Temperature | None = None
    MaxTemp: Temperature | None = None
    Temp9am: Temperature | None = None
    Temp3pm: Temperature | None = None
    Rainfall: NonNegativeMeasurement | None = None
    Evaporation: NonNegativeMeasurement | None = None
    Sunshine: Annotated[
        float, Field(ge=0, le=24, allow_inf_nan=False)
    ] | None = None
    WindGustDir: WindDirection | None = None
    WindGustSpeed: NonNegativeMeasurement | None = None
    WindDir9am: WindDirection | None = None
    WindDir3pm: WindDirection | None = None
    WindSpeed9am: NonNegativeMeasurement | None = None
    WindSpeed3pm: NonNegativeMeasurement | None = None
    Humidity9am: Humidity | None = None
    Humidity3pm: Humidity | None = None
    Pressure9am: Pressure | None = None
    Pressure3pm: Pressure | None = None
    Cloud9am: CloudCover | None = None
    Cloud3pm: CloudCover | None = None


class PredictionResponse(BaseModel):
    """Prediction returned from the saved RainWise model bundle."""

    prediction: Literal["Yes", "No"]
    rain_probability: Annotated[float, Field(ge=0, le=1)]
    threshold: Annotated[float, Field(ge=0, le=1)]
    positive_class: Literal["Yes"]


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
